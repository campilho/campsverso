# Processos do Campsverso para desenvolvimento (plano do M2, decisão 5; gateway no M4). `make run` sobe o NATS
# em segundo plano e estes processos com o honcho, que lê as senhas de .env. Ctrl+C derruba todos.
# Para derrubar um só (critério A6), rode cada um no seu terminal: `uv run honcho start kernel`.
kernel: uv run --locked python -m campsverso_kernel.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml
perception: uv run --locked python -m campsverso_perception.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml
controller: uv run --locked python -m campsverso_controller_runner.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml --controller ${SCRIPT:-farmer}
archiver: uv run --locked python -m campsverso_archiver.main --env config/env/local.yaml
gateway: uv run --locked python -m campsverso_gateway.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml
budget: uv run --locked python -m campsverso_budget.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml
# A mente (ADR-0059) fica desligada no mundo oficial, que segue com o script; para ver o LLM no Camps, use
# `make sandbox MENTE=camps`. Para ligá-la aqui, descomente a linha (e tenha ANTHROPIC_API_KEY no .env):
# mind: uv run --locked python -m campsverso_controller_runner.main --env config/env/local.yaml --world config/worlds/${MUNDO:-farm-camps-01}.yaml --mind camps
