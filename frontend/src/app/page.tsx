const workflow = [
  "Case intake",
  "Image observation",
  "Follow-up questions",
  "Evidence retrieval",
  "Differential report",
];

export default function Home() {
  return (
    <main>
      <div className="shell">
        <h1>FinSight</h1>
        <p className="muted">
          Nile tilapia diagnostic triage skeleton. Frontend screens will connect
          to the FastAPI case endpoints as they are implemented.
        </p>
        <section className="grid" aria-label="Workflow">
          {workflow.map((item, index) => (
            <article className="panel" key={item}>
              <strong>{index + 1}. {item}</strong>
              <p className="muted">Pending implementation</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
