# Nexora Dot X Models
Nexora uses a provider-neutral Model Bus. LiteRT-LM is the first-class local runtime.
## Local model lifecycle
1. Scan the configured model directory for .litertlm.
2. Import or copy a verified local model.
3. Register it in the persistent model registry.
4. Test with the real LiteRT-LM Engine.
5. Benchmark when required.
6. Select a model through routing policy.
Network model downloads are disabled when NEXORA_LOCAL_ONLY=true. Remote downloads require explicit configuration.
