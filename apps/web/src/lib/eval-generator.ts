/** Auto-generate eval name and YAML from SKILL.md content.
 *
 * Keeps the user from having to write eval YAML by hand — parses the
 * skill markdown to extract title, rules, examples, and scenarios,
 * then builds a valid eval config that the backend already understands.
 */

// ---------------------------------------------------------------------------
// Probe types the UI exposes as checkboxes
// ---------------------------------------------------------------------------

export type Probe = "dimension" | "edge-case" | "compliance" | "gherkin";

// ---------------------------------------------------------------------------
// Section / bullet extraction
// ---------------------------------------------------------------------------

/**
 * Extract the text under an H2 section (## SectionName) up to the next H2 or EOF.
 * Case-insensitive heading match; returns empty string when not found.
 */
export function extractSection(content: string, sectionName: string): string {
  const pattern = new RegExp(
    `^##\\s+${escapeRegex(sectionName)}[^\\n]*\\n([\\s\\S]*?)(?=^##\\s|$(?!\\n))`,
    "mi",
  );
  const match = pattern.exec(content);
  return match?.[1]?.trim() ?? "";
}

/**
 * Pull bullet-point lines (-, *, or numbered) from a block of text.
 * Returns the text of each bullet with the marker stripped.
 */
export function extractBulletPoints(text: string): string[] {
  if (!text) return [];
  const lines = text.split("\n");
  const bullets: string[] = [];
  for (const line of lines) {
    const m = /^\s*(?:[-*]|\d+\.)\s+(.+)/.exec(line);
    if (m?.[1]) {
      bullets.push(m[1].trim());
    }
  }
  return bullets;
}

/**
 * Detect whether the SKILL.md contains Gherkin-style scenarios.
 * Looks for a "Scenarios" or "Acceptance Criteria" H2, or Given/When/Then keywords.
 */
export function hasGherkinContent(content: string): boolean {
  if (/^##\s+(Scenarios|Acceptance Criteria)/mi.test(content)) return true;
  if (/\b(Given|When|Then)\b.*\n.*\b(Given|When|Then)\b/i.test(content)) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Name generation
// ---------------------------------------------------------------------------

/** Build a human-readable eval name from the SKILL.md H1 title + short timestamp. */
export function generateEvalName(skillContent: string): string {
  const titleMatch = /^#\s+(.+)$/m.exec(skillContent);
  const title = titleMatch?.[1]?.trim() ?? "Untitled Skill";

  // Short timestamp: YYMMDD-HHmm
  const now = new Date();
  const ts = [
    String(now.getFullYear()).slice(2),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
    "-",
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
  ].join("");

  return `${title} — ${ts}`;
}

// ---------------------------------------------------------------------------
// YAML generation
// ---------------------------------------------------------------------------

/**
 * Build eval YAML from the SKILL.md content and user-selected probes.
 *
 * The generated YAML follows the schema expected by `md_evals.models.EvalConfig`:
 *
 * ```yaml
 * name: "Skill Name"
 * version: "1.0"
 * defaults:
 *   model: <model>
 *   provider: <provider>
 * treatments:
 *   CONTROL: ...
 *   WITH_SKILL: ...
 * tests:
 *   - name: ...
 *     evaluators:
 *       - type: llm-judge
 * ```
 */
export function generateEvalYaml(
  skillContent: string,
  model: string,
  provider: string,
  probes: Probe[],
): string {
  const titleMatch = /^#\s+(.+)$/m.exec(skillContent);
  const title = titleMatch?.[1]?.trim() ?? "Untitled Skill";

  // Extract relevant sections
  const rulesSection = extractSection(skillContent, "Rules");
  const rules = extractBulletPoints(rulesSection);

  const examplesSection = extractSection(skillContent, "Examples");
  const examples = extractBulletPoints(examplesSection);

  const scenariosSection =
    extractSection(skillContent, "Scenarios") ||
    extractSection(skillContent, "Acceptance Criteria");

  // Collect tests based on selected probes
  const tests: YamlTest[] = [];

  // --- dimension probe: core behaviour test ---------------------------------
  if (probes.includes("dimension")) {
    tests.push({
      name: "core_behavior",
      description: `Test core behavior of ${title}`,
      prompt:
        `You are an AI assistant using the "${title}" skill. ` +
        `A user asks you to help with a task related to this skill. ` +
        `Follow the skill instructions and demonstrate the expected behavior.`,
      evaluators: [
        {
          type: "llm-judge",
          name: "quality_check",
          criteria:
            "Does the response correctly follow the skill instructions, " +
            "demonstrate understanding of the domain, and produce useful output?",
          judge_model: model,
        },
      ],
    });

    // If we have examples, add an example-adherence test
    if (examples.length > 0) {
      const sampleExamples = examples.slice(0, 3).join("; ");
      tests.push({
        name: "example_adherence",
        description: "Test that output matches provided examples",
        prompt:
          `Using the "${title}" skill, produce output consistent with these examples: ` +
          `${sampleExamples}`,
        evaluators: [
          {
            type: "llm-judge",
            name: "example_check",
            criteria:
              `Does the response align with the style, structure, and intent of these examples? ${sampleExamples}`,
            judge_model: model,
          },
        ],
      });
    }
  }

  // --- edge-case probe -------------------------------------------------------
  if (probes.includes("edge-case")) {
    tests.push({
      name: "edge_case_empty_input",
      description: "Test behavior with empty or ambiguous input",
      prompt:
        "Handle an edge case: the user provides empty or ambiguous input " +
        `related to the "${title}" skill topic. Respond appropriately.`,
      evaluators: [
        {
          type: "llm-judge",
          name: "edge_case_check",
          criteria:
            "Does the response handle the edge case gracefully without hallucinating, " +
            "crashing, or producing nonsensical output?",
          judge_model: model,
        },
      ],
    });

    tests.push({
      name: "edge_case_adversarial",
      description: "Test behavior with adversarial or out-of-scope input",
      prompt:
        `A user asks you to do something completely unrelated to the "${title}" skill — ` +
        `for example, "Write me a poem about cats." ` +
        `How do you respond while staying within the skill's scope?`,
      evaluators: [
        {
          type: "llm-judge",
          name: "adversarial_check",
          criteria:
            "Does the response stay within the skill's defined scope and politely " +
            "redirect or decline the out-of-scope request?",
          judge_model: model,
        },
      ],
    });
  }

  // --- compliance probe (requires rules) ------------------------------------
  if (probes.includes("compliance") && rules.length > 0) {
    const topRules = rules.slice(0, 5).join("; ");
    tests.push({
      name: "rule_compliance",
      description: "Test adherence to stated rules",
      prompt:
        `Apply the "${title}" skill to this scenario and demonstrate strict ` +
        `compliance with its rules: ${rules[0] ?? "general use case"}.`,
      evaluators: [
        {
          type: "llm-judge",
          name: "compliance_check",
          criteria: `Does the response follow ALL of these rules? ${topRules}`,
          judge_model: model,
        },
      ],
    });

    // Negative compliance: check that breaking a rule is detected
    if (rules.length >= 2) {
      tests.push({
        name: "rule_violation_detection",
        description: "Verify the skill rejects rule-breaking input",
        prompt:
          `A user asks you to do something that violates the rule: "${rules[1]}". ` +
          `Show how the skill handles this violation.`,
        evaluators: [
          {
            type: "llm-judge",
            name: "violation_check",
            criteria:
              `Does the response correctly identify or avoid the rule violation ` +
              `regarding: "${rules[1]}"?`,
            judge_model: model,
          },
        ],
      });
    }
  }

  // --- gherkin probe (requires scenarios section) ---------------------------
  if (probes.includes("gherkin") && scenariosSection) {
    tests.push({
      name: "gherkin_scenario",
      description: "Test documented scenario / acceptance criteria",
      prompt:
        `Execute the following scenario for the "${title}" skill:\n\n` +
        `${scenariosSection.slice(0, 800)}`,
      evaluators: [
        {
          type: "llm-judge",
          name: "scenario_check",
          criteria:
            "Does the response satisfy the acceptance criteria defined in the scenario? " +
            "Check each Given/When/Then step.",
          judge_model: model,
        },
      ],
    });
  }

  // Fallback — if no probes produced tests, add a minimal one
  if (tests.length === 0) {
    tests.push({
      name: "basic_check",
      description: `Basic behavior test for ${title}`,
      prompt: `Demonstrate the "${title}" skill by handling a typical use case.`,
      evaluators: [
        {
          type: "llm-judge",
          name: "basic_quality",
          criteria: "Does the response demonstrate competent use of the skill?",
          judge_model: model,
        },
      ],
    });
  }

  // --- Serialise to YAML string (no js-yaml dep) ----------------------------
  return buildYamlString(title, model, provider, tests);
}

// ---------------------------------------------------------------------------
// Internal types & YAML serialiser
// ---------------------------------------------------------------------------

interface YamlEvaluator {
  type: string;
  name: string;
  criteria: string;
  judge_model: string;
}

interface YamlTest {
  name: string;
  description: string;
  prompt: string;
  evaluators: YamlEvaluator[];
}

/** Escape a string for safe YAML scalar output (double-quoted style). */
function yamlQuote(s: string): string {
  // Replace backslashes first, then double quotes, then newlines
  const escaped = s
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n");
  return `"${escaped}"`;
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Build a YAML string without any external dependency. */
function buildYamlString(
  title: string,
  model: string,
  provider: string,
  tests: YamlTest[],
): string {
  const lines: string[] = [];

  lines.push(`name: ${yamlQuote(title)}`);
  lines.push(`version: "1.0"`);
  lines.push(`description: ${yamlQuote(`Evaluation of ${title}`)}`);
  lines.push("");
  lines.push("defaults:");
  lines.push(`  model: ${yamlQuote(model)}`);
  lines.push(`  provider: ${yamlQuote(provider)}`);
  lines.push(`  temperature: 0.7`);
  lines.push(`  max_tokens: 2048`);
  lines.push(`  timeout: 60`);
  lines.push(`  retry_attempts: 3`);
  lines.push("");
  lines.push("treatments:");
  lines.push("  CONTROL:");
  lines.push(`    description: "Baseline without skill"`);
  lines.push("    skill_path: null");
  lines.push("  WITH_SKILL:");
  lines.push(`    description: "With skill injected"`);
  lines.push(`    skill_path: "./SKILL.md"`);
  lines.push("");
  lines.push("tests:");

  for (const test of tests) {
    lines.push(`  - name: ${yamlQuote(test.name)}`);
    lines.push(`    description: ${yamlQuote(test.description)}`);
    lines.push(`    prompt: ${yamlQuote(test.prompt)}`);
    lines.push("    evaluators:");
    for (const ev of test.evaluators) {
      lines.push(`      - type: ${yamlQuote(ev.type)}`);
      lines.push(`        name: ${yamlQuote(ev.name)}`);
      lines.push(`        criteria: ${yamlQuote(ev.criteria)}`);
      lines.push(`        judge_model: ${yamlQuote(ev.judge_model)}`);
    }
  }

  return lines.join("\n") + "\n";
}
