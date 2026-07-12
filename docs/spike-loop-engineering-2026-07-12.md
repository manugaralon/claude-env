# Spike — Loop Engineering (2026-07-12)

**Origen:** IG [DZZzd9msHJY](https://instagram.com/p/DZZzd9msHJY/) (verdict `research-only`, batch 3). Tesis Steinberger/Cherny: "no promptees agentes, diseña loops que los prompteen". 5 bloques: automations (heartbeat) / worktrees / skills / verification / memory.

**Pregunta del spike:** ¿qué falta en el env para hacer loop engineering, y merece la pena construirlo ahora?

---

## 1. Los 5 bloques vs este env

| Bloque | Estado aquí | Evidencia |
|---|---|---|
| Worktrees | ✅ cubierto | EnterWorktree, isolation worktree en workflows/agents, GSD branching |
| Skills | ✅ cubierto | ~/.claude curado por probation-data + claude-env bootstrap/augment (Phase 7) |
| Verification | ✅ **por delante de la curva** | GSD verifier goal-backward + quality-gate + ciclos adversariales (lección green-mocks ×5 en Clibit) |
| Memory | ✅ cubierto | memoria file-based por proyecto + claude-mem + lessons/instincts |
| **Automations (heartbeat)** | ❌ **el delta real** | 0 crons programados, 0 loops; único heartbeat existente es externo (cron-job.org para outbox drain de Clibit) |

Conclusión parcial: 4/5 ya están. El spike se reduce al bloque heartbeat.

## 2. Primitivos disponibles para el heartbeat (verificado contra docs oficiales code.claude.com, 2026-07-12)

| Primitivo | Sobrevive cerrar terminal | Modelo/permisos | Budget control | Notas |
|---|---|---|---|---|
| Session crons (CronCreate, `/loop 5m …`) | ❌ (salvo `--resume`; expiran 7d) | hereda sesión | ninguno | jitter hasta 30min; fire entre turnos |
| `/loop` dinámico (ScheduleWakeup) | ❌ | hereda sesión | auto-stop del agente | delay 1m–1h elegido por Claude; attended por diseño |
| Workflows | ❌ (nueva sesión = arranca de cero) | por-agente configurable | caps de agentes (16 conc / 1000 total), no tokens | |
| **Routines (cloud)** | ✅ | config propia | **sin cap de tokens por run** | cada run = sesión nueva; el único unattended real |
| Desktop scheduled tasks | ✅ mientras la app esté abierta | — | — | |
| Headless `claude -p` + timer externo (systemd/cron) | ✅ | flags por invocación | `--max-turns N` (turnos, no tokens); bg agents cap 10min | único camino unattended con control aproximado de gasto |
| GitHub Actions (`claude-code-action@v1`) | ✅ | API key | por-token API | **billing API directo, no suscripción** → el más caro |

**Hallazgos clave:**
1. **"Automations" como feature no existe** en docs oficiales — es vocabulario de influencer para crons/routines. No perseguir un feature fantasma.
2. **No existe presupuesto de tokens por run** en NINGÚN primitivo unattended. Solo `--max-turns`, timeouts y caps de workspace (Console, team-level).
3. Contexto de coste (verificado por web, 2026-07-12): el +50% de límites semanales acaba **13 julio 6PM PDT** y Fable 5 sale de los planes tras el 12 julio (→ créditos $10/M in / $50/M out; Anthropic dice que volverá "cuando haya capacidad"). **Loops desatendidos son el patrón más quota-hambriento justo cuando la quota se encoge un tercio.**

## 3. Escalera de loops (framework de decisión)

Antes de programar un loop, subir escalón a escalón — parar en el más bajo que resuelva:

0. **¿Necesita LLM siquiera?** El probation report es un script bash. El lag-alert del outbox de Clibit es cron-job.org + un endpoint. La mayoría de heartbeats son plumbing, no inteligencia.
1. **Event-driven > time-driven.** Los hooks (precommit quality-gate, guards GSD) YA son loops en el sentido Steinberger: disparan en el boundary correcto sin polling ni tokens de reloj.
2. **`/loop` dinámico in-session** para babysitting attended (CI, deploys, PR largo). Coste marginal, cero infra nueva. → **adoptar como hábito.**
3. **`claude -p --max-turns N` + tier económico + systemd timer** — único unattended con control de gasto aproximado. Contra: la VM de dev es limitada (misma razón del no-localhost) y el control es por turnos, no tokens.
4. **Cloud routines** — el candidato estructural. Contra hoy: sin cap de tokens por run + límites recortándose. → **revisit, no adopt.**

## 4. Veredicto

**NO construir loops programados ahora.** El env ya hace loop engineering donde importa (una phase GSD ES un loop con verificación; el heartbeat de prod ya existe fuera, gratis). El único gap con ROI inmediato es de hábito, no de tooling: usar `/loop` dinámico en sesiones largas de babysitting.

**Triggers de revisión:**
- Fable vuelve a los planes / límites normalizan → re-evaluar routines para: revisión mensual de entries `reconsider` en EVALUATIONS.md, informe periódico de skill-usage (o convertir ambos a escalón 0: script + notificación).
- Aparece tarea recurrente real que exija juicio LLM sin humano delante.
- Routines ganan cap de tokens por run → baja el riesgo estructural del escalón 4.

---

## Parte 2 — Implementación de los escalones baratos (2026-07-12, misma sesión)

### Escalón 0 — SHIPPED: `env-heartbeat` (cero tokens)

Las dos tareas recurrentes identificadas ya tienen loop sin LLM:

- **Script**: `~/.claude/scripts/env-heartbeat.sh` — informe semanal a `~/.claude/instrumentation/heartbeat/YYYY-MM-DD.md` + notify-send. Cubre: (1) skill usage últimos 30 días (del log de instrumentación), (2) tamaño de quarantine + alarma cuando venza la review de borrado (2026-08-11), (3) colas `queued`/`reconsider` de EVALUATIONS.md.
- **Units**: `~/.config/systemd/user/env-heartbeat.{service,timer}` — lunes 09:30, `Persistent=true` (catch-up si el equipo estaba apagado).
- **Estado**: script validado con run manual (primer informe ya útil: 6 queued + 4 reconsider acumulados). **Timer escrito pero NO activado** — el harness bloqueó (correctamente) que un agente active persistencia; la activa el humano:
  ```
  systemctl --user enable --now env-heartbeat.timer
  ```

### Escalón 3 — probe empírico: hallazgo de auth

`claude -p --model haiku --max-turns 2` desde subproceso devuelve **"Not logged in"** pese a `~/.claude/.credentials.json` válido (OAuth Max, scopes correctos, sin expirar). La sesión interactiva OAuth no sirve para headless: **los runs no-interactivos en suscripción requieren `claude setup-token`** (token de larga duración) o `ANTHROPIC_API_KEY`. Implicaciones:

1. Un timer con `claude -p` mal autenticado **falla en ~1s sin quemar tokens** — failure mode barato y ruidoso, no silencioso.
2. Antes de cualquier loop unattended con LLM: correr `claude setup-token` una vez y verificar `claude -p "OK"` desde terminal limpia. Sin eso, el escalón 3 no existe en esta máquina.
3. Coste del probe fallido: 0 tokens. El dato de coste real por run queda pendiente del setup-token (no urgente — el veredicto sigue siendo no-unattended-ahora).

*Spike cerrado 2026-07-12 (partes 1+2). Coste: 2 búsquedas web + 1 agente claude-code-guide (~80k tokens subagente) + 0 tokens en probes.*
