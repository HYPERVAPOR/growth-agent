# Prompt Templates

This directory contains prompt templates used by the Growth Agent system.

## Structure

```
prompts/
├── content_evaluation.txt          # System prompt for evaluating content quality
├── content_evaluation_user.txt     # User prompt template for evaluation
├── blog_generation.txt             # System prompt for blog generation
└── blog_generation_user.txt        # User prompt template for blog generation
```

## Template Variables

Templates use Python's `str.format()` syntax for variable substitution.

### content_evaluation.txt

**Variables**: None (static system prompt)

### content_evaluation_user.txt

**Variables**:
- `{author}` - Content author name
- `{source}` - Content source (X/RSS)
- `{content}` - Content text to evaluate

### blog_generation.txt

**Variables**:
- `{context}` - Company/product context for the blog

### blog_generation_user.txt

**Variables**:
- `{content_blocks}` - Formatted curated content items

## Customization

### Editing Prompts

Simply edit the `.txt` files to customize prompts. Changes take effect immediately on next workflow run.

**Example**: Adjust evaluation criteria

Edit `prompts/content_evaluation.txt`:
```
Evaluate content based on:
1. **Technical Depth**: Implementation details and code quality
2. **Innovation**: Novel approaches and creative solutions
3. **Scalability**: Production-ready considerations
4. **Security**: Best practices and vulnerability analysis

Scoring Guidelines:
- 95-100: Production-ready, innovative, secure
- 85-94: High quality with minor improvements needed
- 70-84: Good approach, some refinement needed
- 50-69: Basic implementation, significant gaps
- 0-49: Not recommended
```

### Adding New Prompts

1. Create new `.txt` file in this directory
2. Use `{variable}` syntax for dynamic content
3. Update code to load the new prompt:

```python
from growth_agent.core.prompts import PromptLoader

loader = PromptLoader(Path("prompts"))
prompt = loader.load("your_new_prompt", variable1="value1", variable2="value2")
```

## Best Practices

1. **Be Specific**: Clear instructions produce better results
2. **Use Examples**: Include examples in prompts for complex tasks
3. **Set Constraints**: Specify output format, length, style
4. **Test Changes**: Run workflow with sample data after changes
5. **Version Control**: Track prompt iterations with git

## Language Support

Prompts can be in any language. The system defaults to English, but you can:

1. Translate prompts to Chinese or other languages
2. Add language-specific prompts (e.g., `blog_generation_zh.txt`)
3. Use `{language}` variable to switch between language variants

## Testing Prompts

Test prompt changes without running full workflow:

```python
from growth_agent.config import get_settings
from growth_agent.core.prompts import PromptLoader

settings = get_settings()
loader = PromptLoader(settings.prompts_dir)

# Load and inspect
prompt = loader.load("content_evaluation")
print(prompt)
```

## Fallback Behavior

If prompt files are not found, the system falls back to default prompts hardcoded in the Python code. This ensures the system continues working even if files are missing.
