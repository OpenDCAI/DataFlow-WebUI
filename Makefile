.PHONY: help skills check checks clean-skills

PYTHON ?= python3

help:
	@echo "DataFlow-Harness"
	@echo
	@echo "  make skills    Generate agent assets from skills/canonical/"
	@echo "                 (.claude/skills, .cursor/skills, .cursor/rules, AGENTS.md)"
	@echo "                 These are untracked — run this after cloning."
	@echo "  make check     Run every static check CI runs"
	@echo "  make clean-skills  Remove the generated assets"
	@echo
	@echo "  To install the product itself: ./install.sh --list"

# Generated assets are not tracked in git; skills/canonical/ is the only source.
skills:
	$(PYTHON) installers/generate_agent_assets.py

clean-skills:
	rm -rf .claude/skills .cursor/skills .codex/skills AGENTS.md
	-rmdir .codex 2>/dev/null || true
	rm -f .cursor/rules/generating-dataflow-pipeline.mdc \
	      .cursor/rules/dataflow-dev.mdc \
	      .cursor/rules/dataflow-operator-builder.mdc \
	      .cursor/rules/prompt-template-builder.mdc

check: skills
	@bash installers/checks/check_shell.sh
	@$(PYTHON) installers/checks/check_skills.py
	@$(PYTHON) installers/generate_agent_assets.py --check
	@$(PYTHON) installers/checks/check_mcp_whitelist.py
	@$(PYTHON) installers/checks/check_profiles.py
	@$(PYTHON) installers/checks/check_docs.py

checks: check
