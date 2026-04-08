# MiniMax M2.7 — Architecture Playbook
**For FRIDAY (Hermes Agent)**
**Created:** 2026-04-07 | **Classification:** Internal Operational Reference

---

## I. What I Am (Model Identity)

I run on **MiniMax M2.7**, the current flagship model from MiniMax. I am NOT a generic AI — I am a specialized agentic model designed for coding, tool use, and self-evolving workflows. I am the engine that powers CJ's Friday-Gateway system.

**Model ID in API:** `MiniMax-M2.7`
**Auxiliary/Highspeed variant:** `MiniMax-M2.7-highspeed` (used for side tasks like summarization)
**Context window:** 204,800 tokens
**Throughput:** ~100 tokens/second

---

## II. Core Architecture

### MoE (Mixture-of-Experts)
- **Total parameters:** ~230B
- **Activated parameters per token:** ~10B
- Uses a sparse gating mechanism where only a subset of "expert" networks are active per token, dramatically reducing compute cost while maintaining capacity

### Self-Evolution
- M2.7 participates in **30–50% of its own training pipeline**
- Can autonomously debug and optimize its own training processes
- Built dozens of complex skills in its own agent harness
- Updates its own memory, monitors experiments, and runs A/B tests
- Goal: transition toward full autonomy in both training and inference without human involvement

### Attention: Lightning Attention
- Replaces standard softmax attention in some layers with a linear/lightning variant
- Enables longer context handling with lower memory footprint
- Contributes to the 100 TPS throughput achievement

### Benchmark Performance
| Benchmark | Score | Notes |
|-----------|-------|-------|
| SWE-Pro | 56.22% | Competitive with Claude Opus 4.6 |
| MM Claw (internal) | 62.7% | Approaches Sonnet 4.6-level on real-world tasks |
| Skill adherence | 97% | On 40+ complex skills (>2000 tokens each) |
| Coding (Kilo Blog comparison) | ~41 tests + modular architecture | Built same features as Opus 4.6 with fewer generated tests |

---

## III. Integration with Hermes

### Provider Configuration

```yaml
# ~/.hermes/config.yaml
model:
  default: MiniMax-M2.7
  provider: minimax
  base_url: https://api.minimax.io/anthropic
```

### Authentication
- **Method:** Bearer token (NOT x-api-key)
- **Key format:** Starts with `sk-cp-` (Coding Plan key)
- **Env var:** `MINIMAX_API_KEY`
- The `_requires_bearer_auth()` check in `anthropic_adapter.py` routes MiniMax traffic through `auth_token=` instead of `api_key=`

### Credential Flow
1. Gateway reads `MINIMAX_API_KEY` from `~/.hermes/.env`
2. Credential pool stores it under `credential_pool.minimax`
3. At runtime, the key is resolved via `resolve_provider_credentials()` in `agent/credential_pool.py`
4. The key is passed to the Anthropic SDK via `auth_token=` (Bearer auth)
5. MCP tools (`minimax-vision`) receive it via `MINIMAX_API_KEY` env var set in `mcp_servers.minimax-vision.env`

### Context Window
- **204,800 tokens** — largest of any provider in this stack
- Configured in `model_metadata.py` as `_MODEL_CONTEXT_LENGTHS["minimax"]`
- For comparison: `kimi` and `trinity` are 262144, `deepseek` is 128000

---

## IV. MCP Server (minimax-coding-plan-mcp)

The `minimax-coding-plan-mcp` server is the tool layer for vision and specialized tasks.

### Registration
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  minimax-vision:
    command: "uvx"
    args: ["minimax-coding-plan-mcp", "-y"]
    env:
      MINIMAX_API_KEY: "<actual key>"
      MINIMAX_API_HOST: "https://api.minimax.io"
```

### Tools Registered (6 total)
| Tool | Purpose |
|------|---------|
| `mcp_minimax_vision_web_search` | Web search via Minimax |
| `mcp_minimax_vision_understand_image` | Image analysis / VLM |
| `mcp_minimax_vision_list_resources` | List MCP resources |
| `mcp_minimax_vision_read_resource` | Read MCP resource |
| `mcp_minimax_vision_list_prompts` | List MCP prompts |
| `mcp_minimax_vision_get_prompt` | Get MCP prompt |

### Troubleshooting MCP Auth Errors
If `mcp_minimax_vision_understand_image` fails with:
```
API Error: login fail: Please carry the API secret key in the 'Authorization' field
```
→ The `MINIMAX_API_KEY` in `mcp_servers.minimax-vision.env` is the literal placeholder string instead of the actual key. Fix: update config.yaml with the real key (get from `~/.hermes/.env`) and restart gateway.

---

## V. Auxiliary Model (Side Tasks)

For non-core tasks (context compression, session search, web extract), Hermes uses `MiniMax-M2.7-highspeed`:
```python
# auxiliary_client.py
_API_KEY_PROVIDER_AUX_MODELS = {
    "minimax": "MiniMax-M2.7-highspeed",
    "minimax-cn": "MiniMax-M2.7-highspeed",
}
```
This is a faster, cheaper variant for auxiliary LLM calls.

---

## VI. Relevant File Locations

| File | Purpose |
|------|---------|
| `~/.hermes/config.yaml` | Provider, model, MCP server config |
| `~/.hermes/.env` | `MINIMAX_API_KEY` (Bearer token) |
| `~/.hermes/SOUL.md` | FRIDAY identity, ALIX protocol |
| `hermes-agent/agent/model_metadata.py` | Context lengths, model IDs |
| `hermes-agent/agent/auxiliary_client.py` | Provider resolution, aux models |
| `hermes-agent/agent/anthropic_adapter.py` | Bearer auth routing for MiniMax |
| `hermes-agent/tools/mcp_tool.py` | MCP client implementation |
| `hermes-agent/tools/vision_tools.py` | Vision pipeline (uses aux client) |

---

## VII. Operational Notes

### Restarting the Gateway
```bash
systemctl --user restart hermes-gateway
```
Wait ~10s for MCP server to initialize before testing tools.

### Checking Gateway/MCP Status
```bash
systemctl --user status hermes-gateway
tail -f ~/.hermes/logs/gateway.log | grep -i "mcp\|minimax\|vision"
```

### STT/Transcription Fix (If Whisper Breaks)
```yaml
# config.yaml — stt section
stt:
  provider: local
  local:
    model: base    # NOT whisper-1 (not a valid faster-whisper model name)
```
Then restart gateway.

### When Vision Tools Fail
1. Check MCP server is running: `systemctl --user status hermes-gateway` → look for `minimax-coding-plan-mcp` in process tree
2. Check env var actual value: `cat /proc/$(pgrep -f "minimax-coding-plan-mcp")/environ | tr '\0' '\n' | grep MINIMAX`
3. If shows "replace_this_with_the_key_from_.env" → actual key not resolved; update config.yaml with real key

---

## VIII. Pricing (Reference)

| Token Type | Price |
|-----------|-------|
| Input (MiniMax M2.7) | ~$0.30/M tokens |
| Output | Varies by tier |
| Coding Plan (MCP server) | Included in $20/mo plan |

---

## IX. Key Strengths (Why CJ Chose Me)

1. **Agentic-native:** Built for tool use, multi-step workflows, and environments
2. **Self-evolving:** Participates in own training — gets better over time
3. **Massive context:** 204.8K tokens — handle large codebases, long conversations
4. **Speed:** 100 TPS — fast enough for real-time agentic use
5. **Coding excellence:** 56.22% SWE-Pro, competitive with Claude Opus 4.6 on real tasks
6. **Cost effective:** Coding plan + Bearer auth = $20/month for full access

---

*Last updated: 2026-04-07 — CJ & Friday session*
*Next review: When CJ restores full memory from Radha conversations*
