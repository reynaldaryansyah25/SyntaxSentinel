import React from "react";
import ReactDOM from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  Brain,
  CheckCircle2,
  CircleDot,
  Code2,
  GitBranch,
  GitMerge,
  Loader2,
  Play,
  ShieldCheck,
  TerminalSquare
} from "lucide-react";
import "./styles.css";

type TimelineItem = {
  label: string;
  detail: string;
  status: "complete" | "active" | "pending";
};

type ManualTriggerResponse = {
  message: string;
  project_id: number;
  pipeline_id: number;
  ref: string;
};

type DashboardRun = {
  status: string;
  pipelineId: string;
  projectId: string;
  ref: string;
  jobId: string;
  startedAt: string;
  rootCause: string;
  errorType: string;
  confidenceScore: number;
  riskLevel: string;
  fileModified: string;
  branchName: string;
  commitMessage: string;
  mrUrl: string;
  pipelineUrl: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

const fallbackRun: DashboardRun = {
  status: "Merge Request opened",
  pipelineId: "2559435167",
  projectId: "82634404",
  ref: "dry-run-syntax-error",
  jobId: "14586674831",
  startedAt: "Live demo run",
  rootCause:
    "The add function definition in app.py was missing a colon at the end of its signature.",
  errorType: "Python syntax error",
  confidenceScore: 1,
  riskLevel: "low",
  fileModified: "app.py",
  branchName: "syntaxsentinel/fix-pipeline-2559435167",
  commitMessage: "Fix pipeline failure 2559435167",
  mrUrl: "https://gitlab.com/reynalaryansyah22/syntaxsentinel-demo/-/merge_requests/1",
  pipelineUrl: "https://gitlab.com/reynalaryansyah22/syntaxsentinel-demo/-/pipelines/2559435167"
};

const timeline: TimelineItem[] = [
  {
    label: "Pipeline failure detected",
    detail: "GitLab reported a failed pytest job.",
    status: "complete"
  },
  {
    label: "Job trace read",
    detail: "SyntaxSentinel retrieved the failing job trace.",
    status: "complete"
  },
  {
    label: "Gemini analysis completed",
    detail: "Root cause and minimal fix plan were generated.",
    status: "complete"
  },
  {
    label: "Safety validation passed",
    detail: "Confidence, scope, and patch size were checked.",
    status: "complete"
  },
  {
    label: "Fix branch created",
    detail: "A SyntaxSentinel branch isolated the generated patch.",
    status: "complete"
  },
  {
    label: "Merge Request opened",
    detail: "Human review remains required before merge.",
    status: "active"
  }
];

function statusTone(status: string) {
  if (status.toLowerCase().includes("open")) return "text-mint bg-emerald-50 ring-emerald-200";
  if (status.toLowerCase().includes("failed")) return "text-coral bg-red-50 ring-red-200";
  return "text-azure bg-blue-50 ring-blue-200";
}

function App() {
  const [run, setRun] = React.useState<DashboardRun>(fallbackRun);
  const [form, setForm] = React.useState({
    project_id: fallbackRun.projectId,
    pipeline_id: fallbackRun.pipelineId,
    ref: fallbackRun.ref
  });
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [notice, setNotice] = React.useState("Using latest successful demo run as fallback data.");

  async function submitManualTrigger(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/manual/heal-pipeline`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Demo-Token": window.localStorage.getItem("syntaxsentinel_demo_token") || ""
        },
        body: JSON.stringify({
          project_id: Number(form.project_id),
          pipeline_id: Number(form.pipeline_id),
          ref: form.ref
        })
      });

      if (!response.ok) {
        throw new Error(`Manual trigger failed with HTTP ${response.status}`);
      }

      const payload = (await response.json()) as ManualTriggerResponse;
      setRun((current) => ({
        ...current,
        status: "Healing process accepted",
        projectId: String(payload.project_id),
        pipelineId: String(payload.pipeline_id),
        ref: payload.ref,
        startedAt: new Date().toLocaleString(),
        pipelineUrl: current.pipelineUrl.includes(String(payload.pipeline_id))
          ? current.pipelineUrl
          : `https://gitlab.com/reynalaryansyah22/syntaxsentinel-demo/-/pipelines/${payload.pipeline_id}`
      }));
      setNotice(payload.message);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to call manual trigger endpoint.");
      setNotice("Backend was not reachable, so the dashboard kept mock fallback data.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <Header />

      <section className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-5 px-4 pb-8 pt-5 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
        <StatusCard run={run} />
        <ManualTriggerCard
          form={form}
          loading={loading}
          error={error}
          notice={notice}
          onFormChange={setForm}
          onSubmit={submitManualTrigger}
        />
      </section>

      <section className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-5 px-4 pb-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
        <TimelineCard items={timeline} />
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <DiagnosisCard run={run} />
          <FixPlanCard run={run} />
          <MergeRequestCard run={run} />
          <SignalCard />
        </div>
      </section>
    </main>
  );
}

function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-ink text-white">
            <ShieldCheck className="h-6 w-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-normal sm:text-2xl">
              SyntaxSentinel
            </h1>
            <p className="text-sm text-slate-600">
              Autonomous CI/CD Pipeline Healing Agent
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Pill icon={<Bot className="h-4 w-4" />} label="Gemini reasoning" />
          <Pill icon={<GitBranch className="h-4 w-4" />} label="GitLab tools" />
          <Pill icon={<ShieldCheck className="h-4 w-4" />} label="Human review" />
        </div>
      </div>
    </header>
  );
}

function Pill({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <span className="inline-flex h-9 items-center gap-2 rounded-full border border-slate-200 bg-white px-3 text-slate-700 shadow-sm">
      {icon}
      {label}
    </span>
  );
}

function StatusCard({ run }: { run: DashboardRun }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-600">
            <Activity className="h-4 w-4" aria-hidden="true" />
            Latest pipeline healing run
          </div>
          <h2 className="text-2xl font-semibold tracking-normal text-ink">{run.status}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            SyntaxSentinel isolated a failed pipeline, generated a safe fix plan, and opened a reviewable Merge Request without auto-merging.
          </p>
        </div>
        <span className={`inline-flex h-9 items-center rounded-full px-3 text-sm font-medium ring-1 ${statusTone(run.status)}`}>
          {run.riskLevel.toUpperCase()} RISK
        </span>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Project" value={run.projectId} />
        <Metric label="Pipeline" value={run.pipelineId} />
        <Metric label="Job" value={run.jobId} />
        <Metric label="Ref" value={run.ref} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function ManualTriggerCard({
  form,
  loading,
  error,
  notice,
  onFormChange,
  onSubmit
}: {
  form: { project_id: string; pipeline_id: string; ref: string };
  loading: boolean;
  error: string;
  notice: string;
  onFormChange: React.Dispatch<React.SetStateAction<{ project_id: string; pipeline_id: string; ref: string }>>;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-600">
            <TerminalSquare className="h-4 w-4" aria-hidden="true" />
            Manual trigger
          </div>
          <h2 className="text-lg font-semibold tracking-normal">Fallback pipeline healing</h2>
        </div>
        <button
          type="button"
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm text-slate-700 transition hover:border-azure hover:text-azure"
          onClick={() => {
            const token = window.prompt("Paste X-Demo-Token for this browser session");
            if (token) window.localStorage.setItem("syntaxsentinel_demo_token", token);
          }}
        >
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          Token
        </button>
      </div>
      <form className="grid gap-3" onSubmit={onSubmit}>
        <LabeledInput
          label="project_id"
          value={form.project_id}
          onChange={(value) => onFormChange((current) => ({ ...current, project_id: value }))}
        />
        <LabeledInput
          label="pipeline_id"
          value={form.pipeline_id}
          onChange={(value) => onFormChange((current) => ({ ...current, pipeline_id: value }))}
        />
        <LabeledInput
          label="ref"
          value={form.ref}
          onChange={(value) => onFormChange((current) => ({ ...current, ref: value }))}
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-1 inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Play className="h-4 w-4" aria-hidden="true" />}
          Trigger healing workflow
        </button>
      </form>
      {error && (
        <div className="mt-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          {error}
        </div>
      )}
      {notice && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
          {notice}
        </div>
      )}
    </section>
  );
}

function LabeledInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input
        className="h-10 rounded-lg border border-slate-300 bg-white px-3 font-mono text-sm outline-none transition focus:border-azure focus:ring-2 focus:ring-blue-100"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function TimelineCard({ items }: { items: TimelineItem[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="mb-5 flex items-center gap-2">
        <CircleDot className="h-5 w-5 text-azure" aria-hidden="true" />
        <h2 className="text-lg font-semibold tracking-normal">Agent Activity Timeline</h2>
      </div>
      <div className="grid gap-3">
        {items.map((item, index) => (
          <div key={item.label} className="grid grid-cols-[32px_1fr] gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  item.status === "complete"
                    ? "bg-emerald-100 text-mint"
                    : item.status === "active"
                      ? "bg-blue-100 text-azure"
                      : "bg-slate-100 text-slate-400"
                }`}
              >
                {item.status === "complete" ? <CheckCircle2 className="h-4 w-4" /> : <CircleDot className="h-4 w-4" />}
              </div>
              {index < items.length - 1 && <div className="h-9 w-px bg-slate-200" />}
            </div>
            <div className="pb-3">
              <p className="font-medium text-ink">{item.label}</p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{item.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function DiagnosisCard({ run }: { run: DashboardRun }) {
  return (
    <InfoCard title="Diagnosis" icon={<Brain className="h-5 w-5" />}>
      <dl className="grid gap-3">
        <Field label="Root cause" value={run.rootCause} />
        <Field label="Error type" value={run.errorType} />
        <Field label="Confidence score" value={`${Math.round(run.confidenceScore * 100)}%`} />
        <Field label="Risk level" value={run.riskLevel} />
      </dl>
    </InfoCard>
  );
}

function FixPlanCard({ run }: { run: DashboardRun }) {
  return (
    <InfoCard title="Fix Plan" icon={<Code2 className="h-5 w-5" />}>
      <dl className="grid gap-3">
        <Field label="File modified" value={run.fileModified} mono />
        <Field label="Branch name" value={run.branchName} mono />
        <Field label="Commit message" value={run.commitMessage} />
      </dl>
    </InfoCard>
  );
}

function MergeRequestCard({ run }: { run: DashboardRun }) {
  return (
    <InfoCard title="Merge Request" icon={<GitMerge className="h-5 w-5" />}>
      <div className="grid gap-3">
        <a className="link-button" href={run.mrUrl} target="_blank" rel="noreferrer">
          Open MR
          <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
        </a>
        <a className="link-button secondary" href={run.pipelineUrl} target="_blank" rel="noreferrer">
          View pipeline
          <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
        </a>
      </div>
    </InfoCard>
  );
}

function SignalCard() {
  return (
    <InfoCard title="Safety Signals" icon={<ShieldCheck className="h-5 w-5" />}>
      <div className="grid gap-2 text-sm text-slate-700">
        <Signal label="No auto-merge" />
        <Signal label="Patch scope validated" />
        <Signal label="Human review required" />
        <Signal label="Dry-run ready" />
      </div>
    </InfoCard>
  );
}

function Signal({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
      <CheckCircle2 className="h-4 w-4 text-mint" aria-hidden="true" />
      {label}
    </div>
  );
}

function InfoCard({
  title,
  icon,
  children
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="mb-4 flex items-center gap-2 text-ink">
        <span className="text-azure">{icon}</span>
        <h2 className="text-lg font-semibold tracking-normal">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className={`mt-1 text-sm leading-6 text-ink ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
