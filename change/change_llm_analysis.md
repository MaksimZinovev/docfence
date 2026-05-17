Yes — clean separation. The CLI becomes the driver, `llm.py` just formats the request, and adapters handle provider differences.

---

**Revised structure:**

```shell
core/
└── llm.py              # formats prompts, parses responses, calls adapter
                        # knows nothing about which provider is being used

adapters/
├── __init__.py         # discovers and returns adapter by name
├── anthropic.py        # calls claude via subprocess: `claude -p "prompt"`
├── openai.py           # calls openai cli: `openai api chat.completions.create`
└── shell.py            # generic: any cli tool that reads stdin, writes stdout
                        # fallback for custom or local providers (ollama, llm, etc)

.speccheck/
└── config.toml         # adapter config — which provider, which model, any flags
```

```toml
# .speccheck/config.toml
[llm]
adapter = "anthropic"       # which adapter to use
model = "claude-sonnet-4"   # passed as a flag to the cli tool
timeout = 30                # seconds before subprocess call is killed
```

---

**`adapters/__init__.py`:**

```python
def get_adapter(config: dict) -> "BaseAdapter":
    """
    Read config["llm"]["adapter"], import and return the matching adapter.
    Raises clear error if adapter name not found — tells user which names
    are valid rather than giving an import traceback.
    """
```

**`adapters/anthropic.py`:**

```python
class AnthropicAdapter:
    def __init__(self, model: str, timeout: int): ...

    def call(self, system_prompt: str, user_content: str) -> str:
        """
        Invokes the claude CLI via subprocess:
          claude --model <model> -p "<system_prompt>\n\n<user_content>"
        Returns raw stdout string.
        Raises RuntimeError on non-zero exit or timeout.
        """
```

**`adapters/shell.py`:**

```python
class ShellAdapter:
    def __init__(self, command: str, timeout: int): ...

    def call(self, system_prompt: str, user_content: str) -> str:
        """
        Runs an arbitrary shell command, pipes system_prompt + user_content
        to stdin, returns stdout. Covers ollama, llm CLI, custom wrappers.
        Command template supports {model} interpolation from config.
        Example config:
          adapter = "shell"
          command = "ollama run {model}"
        """
```

**`core/llm.py`:**

```python
def run_llm_validator(
    prompt_text: str,
    content: str,
    adapter: "BaseAdapter",
    ground_truth: str | None = None,
) -> dict:
    """
    Formats the full prompt (injects content and optional ground_truth
    as labelled blocks), calls adapter.call(), parses the JSON response.
    Returns {"pass": bool, "issues": list[str]}.
    Adapter is injected — llm.py never imports adapters directly.
    """
```

---

**`speccheck.py` — revised `cmd_review`:**

```python
def cmd_review(target: str):
    """
    Loads .speccheck/config.toml, resolves adapter via get_adapter(config),
    passes adapter into run_llm_validator for each llm: block.
    Provider is fully swappable by changing one line in config.toml —
    no code changes needed.
    """
```

---

The key constraint: every adapter must accept `(system_prompt, user_content)` and return a raw string. `llm.py` owns parsing that string into structured results. That way a broken provider response is always caught in one place with a consistent error message.

Implement?
