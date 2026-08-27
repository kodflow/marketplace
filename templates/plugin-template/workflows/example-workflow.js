export const meta = {
  name: 'example-workflow',
  description: "Exemple de workflow : analyse en parallele puis synthese",
  whenToUse: "Remplacer par les conditions reelles de declenchement",
  phases: [
    { title: 'Analyse', detail: 'un agent par cible' },
    { title: 'Synthese', detail: 'consolidation des resultats' },
  ],
}

// `args` contient la valeur passee a l'invocation du workflow.
const targets = Array.isArray(args) ? args : ['.']

phase('Analyse')
const findings = await parallel(
  targets.map((t) => () =>
    agent(`Analyser ${t} et retourner les points notables.`, {
      label: `analyse:${t}`,
      phase: 'Analyse',
    }),
  ),
)

phase('Synthese')
const summary = await agent(
  `Consolider ces analyses en une synthese :\n${findings.filter(Boolean).join('\n---\n')}`,
  { phase: 'Synthese' },
)

return { targets, summary }
