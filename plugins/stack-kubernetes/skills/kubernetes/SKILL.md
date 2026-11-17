---
name: kubernetes
description: Convenções para escrever, testar e revisar manifestos Kubernetes, Helm e Kustomize no fluxo — Deployment com requests/limits, probes (liveness, readiness, startup), securityContext restrito, rollout sem indisponibilidade, HPA e PodDisruptionBudget, ConfigMap e Secret (External Secrets/Sealed Secrets), Service/Ingress, NetworkPolicy, Jobs e migrations, e validação com kubeconform/kubectl diff. Use ao criar ou revisar manifestos, charts ou overlays num projeto com stack kubernetes.
---

# Kubernetes no fluxo

As convenções do **projeto** (Helm × Kustomize, estrutura de overlays por ambiente, GitOps com Argo CD/Flux) vencem estas quando conflitarem. Modelo base: `../../templates/deployment.yaml` (relativo a esta skill).

## Escrever
- **Imagem** com tag imutável (versão ou SHA do commit), nunca `latest`; `imagePullPolicy: IfNotPresent`.
- **Recursos**: `requests` de CPU e memória sempre; `limits` de memória sempre (OOM previsível); limite de CPU conforme a política do cluster (throttling). Valores a partir de medida, não chute.
- **Probes**:
  - `readinessProbe`: a aplicação pode receber tráfego (dependências essenciais ok).
  - `livenessProbe`: o processo travou — leve, **sem** checar dependências externas (senão um banco fora reinicia todos os pods).
  - `startupProbe` para aplicação que demora a subir (JVM, .NET grande), em vez de `initialDelaySeconds` enorme.
- **Segurança** (`securityContext`): `runAsNonRoot: true`, `runAsUser` numérico, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true` (com `emptyDir` para `/tmp`), `capabilities: drop: ["ALL"]`, `seccompProfile: RuntimeDefault`. Nunca `privileged`, `hostNetwork`, `hostPath` sem ADR.
- **Rollout**: `RollingUpdate` com `maxUnavailable: 0`/`maxSurge: 1` em serviço crítico; `minReadySeconds`; `terminationGracePeriodSeconds` maior que o tempo de drenagem; `preStop` com pequena espera se o load balancer demora a tirar o pod.
- **Disponibilidade**: `replicas ≥ 2` em produção, `PodDisruptionBudget`, `topologySpreadConstraints`/anti-afinidade entre nós/zonas, `HorizontalPodAutoscaler` com métrica que reflete carga.
- **Configuração**: ConfigMap para configuração, Secret para segredo — e o Secret vem de **External Secrets/Sealed Secrets/CSI do cofre**, nunca em texto (nem base64) no repositório. Mudança de ConfigMap precisa reiniciar o pod (hash no annotation ou `configMapGenerator`).
- **Rede**: Service `ClusterIP` por padrão; Ingress/Gateway com TLS; `NetworkPolicy` negando por padrão e liberando só o necessário.
- **Migrations**: Job (ou hook `pre-upgrade` do Helm) idempotente, separado do Deployment; nunca migração dentro do `main` de cada réplica.
- **Labels** padrão (`app.kubernetes.io/name`, `instance`, `version`, `part-of`) e `namespace` explícito por ambiente.
- Helm: valores por ambiente em `values-<amb>.yaml`, nada de segredo em values; `helm template` reproduzível. Kustomize: base + overlays, patches pequenos.

## Testar
- Renderizar (`helm template` / `kustomize build`) e validar o esquema: `kubeconform -strict -summary` (ou `kubectl apply --dry-run=server` em cluster de dev).
- Políticas: `kube-linter`/`polaris`/`checkov` se o projeto usa.
- Diferença antes de aplicar: `kubectl diff` (ou o diff do Argo CD/Flux) no ambiente de dev. Aplicar em produção é do usuário/pipeline com aprovação, nunca da sessão.
- Validação no ambiente de dev: rollout completo (`kubectl rollout status`), pods prontos, healthcheck respondendo, logs sem erro.

## Checklist de revisão
1. Tag imutável; requests/limits definidos.
2. Readiness e liveness distintas; liveness não depende de serviço externo; startup probe se o boot é lento.
3. `securityContext` restrito; nada privilegiado ou de host.
4. Rollout sem indisponibilidade; PDB e réplicas ≥ 2 em produção.
5. Nenhum segredo no repositório; ConfigMap com reinício garantido.
6. NetworkPolicy e Ingress com TLS; Service interno por padrão.
7. Migração como Job idempotente; manifestos renderizam e passam no `kubeconform`.
