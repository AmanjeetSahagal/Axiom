from app.services.prompt_renderer import render_template


def test_render_template_replaces_variables():
    rendered = render_template("Q: {{question}} / C: {{context}}", {"question": "What?", "context": "Docs"})
    assert rendered == "Q: What? / C: Docs"
