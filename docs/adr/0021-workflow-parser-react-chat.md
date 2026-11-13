# The parser stays a workflow and code resolves dates; the chat is a ReAct agent

Refines design §6.1 (parsing) and §6.4 (chat). Follows invariant 2.

**Context.** When a message names a day ("Ho comprato il pane giovedì a 3 euro"), the draft must get that exact day. Until prompt v2 the LLM did the date arithmetic itself from "Today is … (Friday)". On the fake set it got 86% of dates right. Date arithmetic is exactly what code should compute, not the LLM. We also asked whether the parser should become a ReAct agent with a date tool. The user's rule: use an agent only where it is really needed, and make the chat a proper agent that decides by itself which sources to use.

**Decision: parser.** The parser stays a fixed LangGraph workflow:

```
retrieve → extract → resolve_dates → validate → (retry once) → draft
```

- The LLM copies the date words verbatim into `date_text` ("ieri", "giovedì", "il 2 novembre", or null). Any date the model computes is ignored.
- `resolve_dates` turns those words into a date with `domain/dates.py`, relative to the send day in Europe/Rome.
- Words the code cannot read with certainty ("la settimana scorsa", or a weekday that contradicts the day number) are never guessed. The line gets today's date as a placeholder, and the draft gets a review note.
- Unclear dates are not retried, because asking the model again cannot make the user's words clearer.

Result on the 40 fake cases with gpt-oss:20b: date accuracy 0.860 → 1.000, and 2.8 → 2.4 s per message.

A ReAct loop was rejected for the parser. Every message needs the same steps in the same order, so letting the model choose steps adds latency (one more model turn per tool call) and new ways to fail, and gains nothing. The date "tool" is a plain function the workflow always calls.

**Decision: chat (v0.6), and the plan agent (v0.5).** These are ReAct agents: the model reasons, chooses a tool, reads the result, and repeats until it can answer. They are built by hand in LangGraph (an `agent` node with `bind_tools`, a `ToolNode`, a conditional edge) rather than with the prebuilt helper, so each part is visible and testable. Questions are open-ended ("how much did I spend on restaurants on trips this year, and is it within the plan?"), so the model must decide which sources to combine. That is where an agent earns its cost. The production guidelines they must follow are in design §6.4.

**Considered:**
- ReAct parser with `resolve_date` and `find_similar_transactions` tools. Rejected: slower and less predictable for a fixed task.
- Asking the model to compute dates with better prompting. Rejected: it breaks invariant 2, and 86% was the ceiling we saw.
- The prebuilt `create_react_agent` for the chat. Rejected for clarity and control, not for capability.

**Open point:** web search for the chat. Invariant 4 limits network calls to Telegram, the relay, price providers and backup targets. Searching online would add a new outbound destination, and queries could leak personal context. To be decided by the user before v0.6. One option is a self-hosted SearXNG, opt-in, with queries stripped of ledger data.
