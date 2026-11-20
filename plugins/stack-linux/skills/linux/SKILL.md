---
name: linux
description: Convenções para configurar, testar e revisar servidores e imagens Linux no fluxo — serviços systemd com usuário próprio e endurecimento, usuários, grupos e permissões mínimas, pacotes e atualizações fixados, SSH só por chave e sem root, firewall, logs no journald com rotação, timers no lugar de cron, sistema de arquivos e disco, diagnóstico (journalctl, ss, df, top) e mudança em produção sempre pelo humano. Use ao criar ou revisar unit files, cloud-init, scripts de provisionamento, runbooks ou configuração de servidor num projeto com stack linux.
---

# Linux no fluxo

As convenções do **projeto** (distribuição, ferramenta de provisionamento — cloud-init, Ansible, Packer —, imagem base corporativa, `infra` do perfil) vencem estas quando conflitarem.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Regra de ouro
**A sessão não altera servidor compartilhado** (homologação, produção) por SSH. Ela escreve a configuração versionada (unit, cloud-init, script, playbook, runbook), testa numa VM/container descartável e entrega o passo a passo — com como verificar e como voltar — para o humano ou o pipeline aplicar.

## Configurar
- **Distribuição e versão** do projeto (`/etc/os-release`); comando de pacote dela (`apt`, `dnf`, `apk`). Sem misturar repositórios de outra distribuição.
- **Pacotes**: instalar só o necessário, versão fixada quando o projeto fixa; repositório de terceiro com chave assinada em `/etc/apt/keyrings` (não `apt-key`); atualizações de segurança automáticas conforme a política do projeto (`unattended-upgrades`, `dnf-automatic`).
- **Serviço da aplicação em systemd**: unit em `/etc/systemd/system/<app>.service` versionada; `User=`/`Group=` próprios (nunca root), `WorkingDirectory`, `ExecStart` com caminho absoluto, `Restart=on-failure`, segredos fora do unit — `LoadCredential=` (systemd 247+, não vira variável de ambiente herdada) ou, se o projeto já usa, `EnvironmentFile=` com permissão `0600`, limites (`LimitNOFILE`, `MemoryMax`). Endurecimento: `NoNewPrivileges=yes`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`, `ReadWritePaths=` só onde escreve; conferir com `systemd-analyze security <app>`.
- **Agendamento**: timer do systemd (`.timer` + `.service`) em vez de cron quando possível (log no journald, `Persistent=true`, sem execução sobreposta). Cron que ficar: caminho absoluto, `PATH` definido, saída para log, lock (`flock`) contra sobreposição.
- **Usuários e permissões**: conta de serviço sem shell de login (`/usr/sbin/nologin`); arquivos da aplicação com dono certo e modo mínimo (`0640`/`0750`); nunca `chmod 777`; `sudo` por regra específica em `/etc/sudoers.d/` (validar com `visudo -c`), sem `NOPASSWD: ALL`.
- **SSH**: só chave (`PasswordAuthentication no`), `PermitRootLogin no`, usuários permitidos explícitos; mudança de `sshd_config` validada com `sshd -t` e testada **numa segunda sessão aberta** antes de fechar a primeira.
- **Rede e firewall**: só as portas necessárias (`ufw`, `firewalld` ou `nftables`, conforme a distribuição); serviço interno escutando em `127.0.0.1` ou na rede privada; conferir com `ss -tlnp`.
- **Logs**: aplicação em stdout/stderr → journald (com limite em `journald.conf`, `SystemMaxUse`); arquivo de log próprio só com `logrotate`. Nada de segredo em log.
- **Disco e arquivos**: dados fora da raiz quando crescem (volume próprio, `/var/lib/<app>`), montagem por `UUID=` no `/etc/fstab` com `nofail` para disco opcional; `fstab` validado com `findmnt --verify` antes de reiniciar.
- **Kernel/sysctl**: ajuste em `/etc/sysctl.d/<nn>-<app>.conf` com comentário do motivo, nunca só em tempo de execução.
- **Fuso e hora**: servidor em UTC com sincronização (`systemd-timesyncd`/`chrony`); a aplicação converte para exibir.
- Scripts de provisionamento seguem a stack `bash`; arquivos versionados seguem a stack `git` (`*.sh` e units em LF).

## Testar
- Aplicar a configuração do zero numa VM ou container descartável da mesma distribuição e versão (cloud-init: `cloud-init schema --config-file`; Ansible: `--check --diff` e Molecule se o projeto usa).
- Sintaxe antes de aplicar: `systemd-analyze verify <unit>`, `sshd -t`, `visudo -c`, `nginx -t`, `findmnt --verify`.
- Serviço: `systemctl status`, `journalctl -u <app> -b`, reinício sobrevivendo (`systemctl restart`, reboot da VM de teste), healthcheck do perfil respondendo.
- Segurança: `systemd-analyze security <app>`, portas com `ss -tlnp`, varredura da imagem/servidor se o projeto tem (Lynis, Trivy).
- Diagnóstico (somente leitura): `journalctl -p err -b`, `systemctl --failed`, `df -h`/`df -i`, `free -m`, `top`/`htop`, `ss -s`, `dmesg -T | tail`.

## Checklist de revisão
1. Distribuição e versão condizem com o projeto e estão com suporte (ver `atual.md`).
2. Serviço com usuário próprio, sem root, segredos fora do unit (`LoadCredential` ou `EnvironmentFile` `0600`) e endurecimento do systemd.
3. Permissões mínimas: nenhum `777`, `sudo` restrito, conta de serviço sem login.
4. SSH só por chave, sem root; firewall com só as portas necessárias; serviço interno sem escutar em `0.0.0.0` à toa.
5. Pacotes de fonte assinada e versão controlada; atualizações de segurança previstas.
6. Logs com limite/rotação e sem segredo; agendamento por timer (ou cron com lock e log).
7. Configuração validada (`systemd-analyze verify`, `sshd -t`, `visudo -c`, `findmnt --verify`) e testada em ambiente descartável.
8. Mudança em servidor compartilhado entregue como passo a passo com verificação e volta, executado pelo humano.
