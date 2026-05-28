import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock3,
  ExternalLink,
  FileCode2,
  GitBranch,
  GitMerge,
  Loader2,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const INITIAL_DEMO_TOKEN = import.meta.env.VITE_DEMO_TOKEN ?? "";

const mockRun = {
  status: "Merge Request opened",
  projectId: 82634404,
  pipelineId: 2559435167,
  jobId: 14586674831,
  ref: "dry-run-syntax-error",
  sourceFilePath: "app.py",
  branchName: "syntaxsentinel/fix-pipeline-2559435167",
  commitMessage: "Fix pipeline failure 2559435167",
  mrUrl:
    "https://gitlab.com/reynalaryansyah22/syntaxsentinel-demo/-/merge_requests/1",
  pipelineUrl:
    "https://gitlab.com/reynalaryansyah22/syntaxsentinel-demo/-/pipelines/2559435167",
  rootCause:
    "The add function definition in app.py is missing a colon at the end of its signature, causing Python to raise SyntaxError: expected ':'.",
  errorType: "Python syntax error",
  confidenceScore: 1,
  riskLevel: "low",
  updatedAt: "2026-05-28 22:46",
};

const timelineItems = [
  {
    label: "Pipeline failure detected",
    icon: AlertTriangle,
    tone: "amber",
  },
  {
    label: "Job trace read",
    icon: FileCode2,
    tone: "sky",
  },
  {
    label: "Gemini analysis completed",
    icon: Brain,
    tone: "indigo",
  },
  {
    label: "Safety validation passed",
    icon: ShieldCheck,
    tone: "emerald",
  },
  {
    label: "Fix branch created",
    icon: GitBranch,
    tone: "cyan",
  },
  {
    label: "Merge Request opened",
    icon: GitMerge,
    tone: "violet",
  },
];

const toneClass = {
  amber: "border-amber-200 bg-amber-50 text-amber-700",
  sky: "border-sky-200 bg-sky-50 text-sky-700",
  indigo: "border-indigo-200 bg-indigo-50 text-indigo-700",
  emerald: "border-emerald-200 bg-emerald-50 text-emerald-700",
  cyan: "border-cyan-200 bg-cyan-50 text-cyan-700",
  violet: "border-violet-200 bg-violet-50 text-violet-700",
};

function App() {
  const [form, setForm] = useState({
    projectId: String(mockRun.projectId),
    pipelineId: String(mockRun.pipelineId),
    ref: mockRun.ref,
    demoToken: INITIAL_DEMO_TOKEN,
  });
  const [latestRun, setLatestRun] = useState(mockRun);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("Using demo data until a live run is triggered.");

  const confidencePercent = useMemo(() => {
    return Math.round((latestRun.confidenceScore ?? 0) * 100);
  }, [latestRun.confidenceScore]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");
    setNotice("");

    const payload = {
      project_id: Number(form.projectId),
      pipeline_id: Number(form.pipelineId),
      ref: form.ref.trim(),
    };

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/manual/heal-pipeline`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(form.demoToken ? { "X-Demo-Token": form.demoToken } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Backend returned HTTP ${response.status}`);
      }

      setLatestRun((current) => ({
        ...current,
        status: "Manual trigger accepted",
        projectId: payload.project_id,
        pipelineId: payload.pipeline_id,
        ref: payload.ref,
        updatedAt: new Date().toLocaleString(),
      }));
      setNotice("Manual healing request accepted. Watch the backend logs for the agent run.");
    } catch (submitError) {
      setError(
        `${submitError.message}. Dashboard tetap memakai mock data agar demo UI bisa dilihat.`,
      );
      setLatestRun(mockRun);
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <main className="min-h-screen bg-[#eef2f7] text-slate-900">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <Header />

        <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <StatusCard latestRun={latestRun} confidencePercent={confidencePercent} />
          <ManualTriggerForm
            form={form}
            isSubmitting={isSubmitting}
            error={error}
            notice={notice}
            onChange={updateForm}
            onSubmit={handleSubmit}
          />
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
          <AgentTimeline />
          <div className="grid gap-5 md:grid-cols-2">
            <DiagnosisCard latestRun={latestRun} confidencePercent={confidencePercent} />
            <FixPlanCard latestRun={latestRun} />
          </div>
        </section>

        <MergeRequestCard latestRun={latestRun} />
      </div>
    </main>
  );
}

function Header() {
  return (
    <header className="flex flex-col gap-4 rounded-lg border border-white/80 bg-white/90 p-5 shadow-panel sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-950 text-white">
          <Sparkles className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">
            SyntaxSentinel
          </h1>
          <p className="mt-1 text-sm font-medium text-slate-600">
            Autonomous CI/CD Pipeline Healing Agent
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
        <Activity className="h-4 w-4" aria-hidden="true" />
        Agent online
      </div>
    </header>
  );
}

function StatusCard({ latestRun, confidencePercent }) {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Latest pipeline healing run
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950">
            {latestRun.status}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Agent membaca job trace, meminta analisis Gemini, membuat patch aman, lalu
            membuka Merge Request untuk direview manusia.
          </p>
        </div>
        <div className="flex min-w-40 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700">
          <Clock3 className="h-4 w-4 text-slate-500" aria-hidden="true" />
          {latestRun.updatedAt}
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Project" value={latestRun.projectId} />
        <Metric label="Pipeline" value={latestRun.pipelineId} />
        <Metric label="Job" value={latestRun.jobId} />
        <Metric label="Confidence" value={`${confidencePercent}%`} />
      </div>
    </section>
  );
}

function AgentTimeline() {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Agent activity timeline
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">
            Self-healing sequence
          </h2>
        </div>
        <RefreshCw className="h-5 w-5 text-slate-400" aria-hidden="true" />
      </div>

      <ol className="grid gap-3 sm:grid-cols-2">
        {timelineItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <li
              className="flex min-h-20 items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3"
              key={item.label}
            >
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${toneClass[item.tone]}`}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Step {index + 1}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-900">
                  {item.label}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function DiagnosisCard({ latestRun, confidencePercent }) {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-950">Diagnosis</h2>
        <Brain className="h-5 w-5 text-indigo-500" aria-hidden="true" />
      </div>

      <div className="mt-5 space-y-4">
        <InfoBlock label="Root cause" value={latestRun.rootCause} />
        <InfoBlock label="Error type" value={latestRun.errorType} />
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Confidence score" value={`${confidencePercent}%`} />
          <Metric label="Risk level" value={latestRun.riskLevel} tone="success" />
        </div>
      </div>
    </section>
  );
}

function FixPlanCard({ latestRun }) {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-950">Fix Plan</h2>
        <ShieldCheck className="h-5 w-5 text-emerald-500" aria-hidden="true" />
      </div>

      <div className="mt-5 space-y-4">
        <InfoBlock label="File modified" value={latestRun.sourceFilePath} mono />
        <InfoBlock label="Branch name" value={latestRun.branchName} mono />
        <InfoBlock label="Commit message" value={latestRun.commitMessage} />
      </div>
    </section>
  );
}

function MergeRequestCard({ latestRun }) {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            GitLab handoff
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">
            Merge Request ready for human review
          </h2>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <ExternalButton href={latestRun.mrUrl} icon={GitMerge}>
            Open MR
          </ExternalButton>
          <ExternalButton href={latestRun.pipelineUrl} icon={Activity}>
            View Pipeline
          </ExternalButton>
        </div>
      </div>
    </section>
  );
}

function ManualTriggerForm({
  form,
  isSubmitting,
  error,
  notice,
  onChange,
  onSubmit,
}) {
  return (
    <section className="rounded-lg border border-white/80 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Manual trigger
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">
            Heal a failed pipeline
          </h2>
        </div>
        <Play className="h-5 w-5 text-sky-500" aria-hidden="true" />
      </div>

      <form className="mt-5 grid gap-4" onSubmit={onSubmit}>
        <Field
          label="project_id"
          inputMode="numeric"
          value={form.projectId}
          onChange={(event) => onChange("projectId", event.target.value)}
        />
        <Field
          label="pipeline_id"
          inputMode="numeric"
          value={form.pipelineId}
          onChange={(event) => onChange("pipelineId", event.target.value)}
        />
        <Field
          label="ref"
          value={form.ref}
          onChange={(event) => onChange("ref", event.target.value)}
        />
        <Field
          label="demo token"
          type="password"
          value={form.demoToken}
          onChange={(event) => onChange("demoToken", event.target.value)}
        />

        <button
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Play className="h-4 w-4" aria-hidden="true" />
          )}
          {isSubmitting ? "Triggering..." : "Trigger healing"}
        </button>
      </form>

      {notice ? (
        <div className="mt-4 flex gap-2 rounded-lg border border-sky-200 bg-sky-50 p-3 text-sm font-medium text-sky-800">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{notice}</span>
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}
    </section>
  );
}

function Field({ label, ...props }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <input
        className="min-h-11 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-900 transition placeholder:text-slate-400 focus:border-sky-400 focus:bg-white"
        required
        {...props}
      />
    </label>
  );
}

function InfoBlock({ label, value, mono = false }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p
        className={`mt-1 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-6 text-slate-800 ${
          mono ? "font-mono" : "font-medium"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function Metric({ label, value, tone = "default" }) {
  const styles =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-slate-200 bg-slate-50 text-slate-900";

  return (
    <div className={`rounded-lg border p-3 ${styles}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-1 break-words text-lg font-semibold tracking-normal">
        {value}
      </p>
    </div>
  );
}

function ExternalButton({ href, icon: Icon, children }) {
  return (
    <a
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
      href={href}
      rel="noreferrer"
      target="_blank"
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      {children}
      <ExternalLink className="h-4 w-4" aria-hidden="true" />
    </a>
  );
}

export default App;
