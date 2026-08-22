# Discovery Skill

## Description
Searches GitHub and the web for relevant products, skills, and resources related to the Preparation Station/TEFA domain.

## Usage
This skill helps discover:
1. GitHub repositories for education/catalog templates
2. Web services for TEFA product listings
3. Agent skills and prompts for automation
4. Design system components and patterns

## Search Directives
- `gh repo search "education catalog"` - Find education catalog repos
- `gh repo search "TEFA vendor"` - Find TEFA vendor repos  
- `web search "Preparation Station products"` - Find product ideas
- `web search "curriculum catalog template"` - Find catalog templates

## Recent Discoveries (2026)
- `warpdotdev/oz-agent-action` - GitHub Actions agent integration
- `anthropics/claude-agent-sdk-python` - Python SDK for Claude Code
- `TEAM-MMM01/hermes-agent` - Growth-with-you agent
- `OpenHands/software-agent-sdk` - Modular agent SDK

## How to Use
1. Run `gh repo search "education catalog --limit 10"` to find repos
2. Use `web search "Preparation Station products"` for product ideas
3. Add discovered skills to `.system/skills/`
4. Update `skills_inventory.md` with new findings
