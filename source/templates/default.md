# [{{ category | upper }}] {{ title }}

- **Категория:** {{ category }}
- **Сложность:** {{ difficulty }}
- **Флаг:** `{{ flag }}`
- **Команда:** {{ team }}
{% if link %}- **Ссылка:** {{ link }}{% endif %}
- **Дата:** {{ date }}

## Описание

{{ description }}

## Решение

{% for step in steps %}
### Шаг {{ loop.index }}: {{ step.title }}

{{ step.description }}

{% if step.commands %}
```bash
{{ step.commands }}
```
{% endif %}
{% endfor %}

## Флаг

`{{ flag }}`
