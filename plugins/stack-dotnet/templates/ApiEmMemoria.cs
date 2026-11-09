using System.Net.Http.Headers;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;
using Xunit;

namespace MeuProjeto.Tests
{
    /// <summary>
    /// Sobe a API inteira (Program/Startup, IoC, JWT, Swagger) num Kestrel local em porta livre, com configuração em
    /// memória e um JWT de teste. Não chama sistemas externos: use corpos que param na validação do modelo.
    /// Uso: <c>public class MeusTestes(ApiEmMemoria api) : IClassFixture&lt;ApiEmMemoria&gt;</c>.
    /// Ajuste: <c>Program.CreateHostBuilder</c> (ou WebApplication), as chaves de configuração do JWT e o ambiente.
    /// </summary>
    public sealed class ApiEmMemoria : IAsyncLifetime
    {
        private const string Emissor = "teste";
        private const string Audiencia = "teste";
        private static readonly string Chave = Convert.ToBase64String(Guid.NewGuid().ToByteArray()) + Guid.NewGuid().ToString("N");

        private IHost? _host;

        public HttpClient Cliente { get; } = new(new HttpClientHandler { AllowAutoRedirect = false });

        /// <summary>Serviços da API em execução (descritores de action, opções de JSON etc.).</summary>
        public IServiceProvider Services => _host!.Services;

        public async Task InitializeAsync()
        {
            _host = Program
                .CreateHostBuilder([])
                .ConfigureAppConfiguration(c =>
                    c.AddInMemoryCollection(
                        new Dictionary<string, string?>
                        {
                            ["Jwt:Key"] = Chave,
                            ["Jwt:Issuer"] = Emissor,
                            ["Jwt:Audience"] = Audiencia,
                            ["Settings:EnableSwagger"] = "true",
                            ["https_port"] = "", // sem redirecionamento para HTTPS
                        }
                    )
                )
                .UseEnvironment("Testes") // sem appsettings de ambiente nem user secrets da máquina
                .ConfigureWebHost(w => w.UseUrls("http://127.0.0.1:0"))
                .Build();
            await _host.StartAsync();

            var endereco = _host.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.First();
            Cliente.BaseAddress = new Uri(endereco);
            Cliente.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", Token());
        }

        public async Task DisposeAsync()
        {
            Cliente.Dispose();
            if (_host != null)
            {
                await _host.StopAsync();
                _host.Dispose();
            }
        }

        private static string Token() =>
            new JsonWebTokenHandler().CreateToken(
                new SecurityTokenDescriptor
                {
                    Subject = new ClaimsIdentity([new Claim("usuario", "teste")]),
                    Issuer = Emissor,
                    Audience = Audiencia,
                    Expires = DateTime.UtcNow.AddMinutes(10),
                    SigningCredentials = new SigningCredentials(
                        new SymmetricSecurityKey(Encoding.UTF8.GetBytes(Chave)),
                        SecurityAlgorithms.HmacSha256
                    ),
                }
            );
    }
}
