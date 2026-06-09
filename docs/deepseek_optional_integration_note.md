# DeepSeek Optional Integration Note

Phase 2-G does not connect to DeepSeek.

## Current status

- The dashboard uses a local deterministic explainer.
- `src/explain/llm_explainer.py` is only a disabled stub.
- No external API calls are made by default.
- No DeepSeek API key is required or read.

## Future optional use

DeepSeek could be used later as a natural-language explanation layer, but the core probability calculation does not depend on it.

A future Phase 2-H would require:

- explicit user authorization;
- a user-provided API key;
- no API key committed to Git;
- clear network failure handling;
- safety filtering before showing generated text;
- output constraints that prevent result guarantees or betting promises.

## Safety

Any future LLM output must remain diagnostic and must not generate wagering promises, payment flows, order placement, proxy purchase features, or guaranteed-outcome language.

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。
