# Processos do Campsverso para desenvolvimento (plano do M2, decisão 5). `make run` sobe o NATS
# em segundo plano e estes processos com o honcho, que lê as senhas de .env. Ctrl+C derruba todos.
# Para derrubar um só (critério A6), rode cada um no seu terminal: `uv run honcho start kernel`.
kernel: uv run --locked python -m campsverso_kernel.main --env config/env/local.yaml --world config/worlds/farm-camps-01.yaml
perception: uv run --locked python -m campsverso_perception.main --env config/env/local.yaml --world config/worlds/farm-camps-01.yaml
controller: uv run --locked python -m campsverso_controller_runner.main --env config/env/local.yaml --world config/worlds/farm-camps-01.yaml --controller farmer
archiver: uv run --locked python -m campsverso_archiver.main --env config/env/local.yaml
