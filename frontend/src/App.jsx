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
  Gauge,
  Loader2,
  RefreshCw,
  ShieldCheck,
  TerminalSquare,
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
  branchName: "syntaxsentinel/fix-pipeline-2559435167-job-14586674831",
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
    detail: "GitLab reported a failed pytest job and marked the pipeline for repair.",
    icon: AlertTriangle,
    tone: "warning",
  },
  {
    label: "Job trace read",
    detail: "SyntaxSentinel collected the trace and extracted candidate file paths.",
    icon: FileCode2,
    tone: "cyan",
  },
  {
    label: "Gemini analysis completed",
    detail: "Gemini generated a root-cause diagnosis and minimal fix plan.",
    icon: Brain,
    tone: "violet",
  },
  {
    label: "Safety validation passed",
    detail: "Patch scope, confidence, risk level, and changed lines were checked.",
    icon: ShieldCheck,
    tone: "success",
  },
  {
    label: "Fix branch created",
    detail: "A dedicated SyntaxSentinel branch was prepared for the repair.",
    icon: GitBranch,
    tone: "cyan",
  },
  {
    label: "Merge Request opened",
    detail: "The generated fix is ready for human review in GitLab.",
    icon: GitMerge,
    tone: "success",
  },
];

const toneStyles = {
  cyan: {
    icon: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200 shadow-cyan-500/10",
    badge: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
    glow: "shadow-cyan-500/10",
  },
  violet: {
    icon: "border-violet-400/30 bg-violet-400/10 text-violet-200 shadow-violet-500/10",
    badge: "border-violet-400/30 bg-violet-400/10 text-violet-200",
    glow: "shadow-violet-500/10",
  },
  success: {
    icon: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200 shadow-emerald-500/10",
    badge: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    glow: "shadow-emerald-500/10",
  },
  warning: {
    icon: "border-amber-400/30 bg-amber-400/10 text-amber-200 shadow-amber-500/10",
    badge: "border-amber-400/30 bg-amber-400/10 text-amber-200",
    glow: "shadow-amber-500/10",
  },
};

const delay = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function playProcessAnimation(setProcessIndex) {
  for (let index = 0; index < timelineItems.length; index += 1) {
    setProcessIndex(index);
    await delay(520);
  }
}

function App() {
  const [form, setForm] = useState({
    projectId: String(mockRun.projectId),
    pipelineId: String(mockRun.pipelineId),
    ref: mockRun.ref,
    demoToken: INITIAL_DEMO_TOKEN,
  });
  const [latestRun, setLatestRun] = useState(mockRun);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runState, setRunState] = useState("idle");
  const [processIndex, setProcessIndex] = useState(timelineItems.length);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(
    "Demo data is loaded. Trigger a run to watch the agent sequence.",
  );

  const confidencePercent = useMemo(() => {
    return Math.round((latestRun.confidenceScore ?? 0) * 100);
  }, [latestRun.confidenceScore]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setRunState("running");
    setProcessIndex(0);
    setError("");
    setNotice("");

    const payload = {
      project_id: Number(form.projectId),
      pipeline_id: Number(form.pipelineId),
      ref: form.ref.trim(),
    };

    const request = fetch(`${API_BASE_URL}/api/v1/manual/heal-pipeline`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(form.demoToken ? { "X-Demo-Token": form.demoToken } : {}),
      },
      body: JSON.stringify(payload),
    });

    try {
      const [response] = await Promise.all([
        request,
        playProcessAnimation(setProcessIndex),
      ]);

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
      setProcessIndex(timelineItems.length);
      setRunState("complete");
      setNotice("Manual healing request accepted. Watch the backend logs for the agent run.");
    } catch (submitError) {
      setProcessIndex(0);
      setRunState("error");
      setLatestRun(mockRun);
      setError(
        `${submitError.message}. Dashboard tetap memakai mock data agar demo UI bisa dilihat.`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <AppShell>
      <HeaderCard runState={runState} />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <div className="grid gap-6">
          <LatestRunCard
            confidencePercent={confidencePercent}
            isSubmitting={isSubmitting}
            latestRun={latestRun}
            processIndex={processIndex}
            runState={runState}
          />
          <AgentTimeline
            isSubmitting={isSubmitting}
            processIndex={processIndex}
            runState={runState}
          />
        </div>

        <ManualTriggerPanel
          error={error}
          form={form}
          isSubmitting={isSubmitting}
          notice={notice}
          onChange={updateForm}
          onSubmit={handleSubmit}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr_0.9fr]">
        <DiagnosisCard confidencePercent={confidencePercent} latestRun={latestRun} />
        <FixPlanCard latestRun={latestRun} />
        <MergeRequestCard latestRun={latestRun} />
      </section>
    </AppShell>
  );
}

function AppShell({ children }) {
  return (
    <main className="premium-shell min-h-screen overflow-hidden bg-[#0B1020] text-slate-100">
      <div className="pointer-events-none fixed inset-0 soft-grid opacity-40" />
      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </div>
    </main>
  );
}

function HeaderCard({ runState }) {
  const isRunning = runState === "running";

  return (
    <header className="relative overflow-hidden rounded-2xl border border-slate-700/40 bg-slate-900/60 p-[1px] shadow-2xl shadow-cyan-500/5 backdrop-blur-xl">
      <div className="header-glow absolute inset-0 opacity-80" />
      <div className="relative rounded-2xl bg-[#101827]/80 p-5 sm:p-6">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="flex items-center gap-4">
            <LogoBadge active={isRunning} />
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-300/80">
                Autonomous CI/CD recovery
              </p>
              <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-50 sm:text-4xl">
                SyntaxSentinel
              </h1>
              <p className="mt-2 max-w-2xl text-sm font-medium leading-6 text-slate-300 sm:text-base">
                Autonomous CI/CD Pipeline Healing Agent
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:w-[380px]">
            <StatusPill
              label="Agent"
              status={isRunning ? "Healing" : "Online"}
              variant="online"
            />
            <StatusPill icon={Gauge} label="Mode" status="Human review" />
          </div>
        </div>
      </div>
    </header>
  );
}

function LogoBadge({ active }) {
  return (
    <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-cyan-300/20 bg-slate-950/80 shadow-2xl shadow-cyan-500/10">
      <div className="absolute inset-1 rounded-[1rem] border border-white/5" />
      <svg
        aria-label="SyntaxSentinel logo"
        className="relative h-12 w-12"
        role="img"
        viewBox="0 0 64 64"
      >
        <path
          d="M32 5 53 15v16c0 13.2-8.8 22.9-21 28-12.2-5.1-21-14.8-21-28V15L32 5Z"
          fill="#111827"
          stroke="#38BDF8"
          strokeWidth="2.8"
        />
        <path
          d="M24 23 17 31l7 8"
          fill="none"
          stroke="#8B5CF6"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />
        <path
          d="m40 23 7 8-7 8"
          fill="none"
          stroke="#38BDF8"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />
        <path
          d="m35 18-7 28"
          fill="none"
          stroke="#F8FAFC"
          strokeLinecap="round"
          strokeWidth="3.5"
        />
        <path
          className={active ? "logo-scan" : ""}
          d="M14 31h36"
          fill="none"
          stroke="#10B981"
          strokeLinecap="round"
          strokeOpacity="0.9"
          strokeWidth="2"
        />
      </svg>
    </div>
  );
}

function LatestRunCard({
  confidencePercent,
  isSubmitting,
  latestRun,
  processIndex,
  runState,
}) {
  const progress =
    runState === "running"
      ? Math.min(((processIndex + 1) / timelineItems.length) * 100, 100)
      : 100;

  return (
    <GlassCard className="relative overflow-hidden p-5 sm:p-6">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/60 to-transparent" />
      <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-start">
        <div>
          <SectionHeader
            kicker="Latest healing run"
            title={isSubmitting ? "Agent healing in progress" : latestRun.status}
          />
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-300">
            The agent watches a failed pipeline, reads the trace, asks Gemini for
            diagnosis, validates safety, then prepares a reviewed GitLab Merge
            Request.
          </p>
        </div>
        <TimestampPill value={latestRun.updatedAt} />
      </div>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-700/40 bg-slate-950/40">
        <div className="h-2 bg-slate-800/80">
          <div
            className={`h-full rounded-r-full bg-gradient-to-r from-cyan-300 via-sky-400 to-violet-400 transition-all duration-500 ${
              isSubmitting ? "progress-stripes" : ""
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="grid gap-px bg-slate-700/25 sm:grid-cols-4">
          <MetricCard label="Project" value={latestRun.projectId} />
          <MetricCard label="Pipeline" value={latestRun.pipelineId} />
          <MetricCard label="Job" value={latestRun.jobId} />
          <MetricCard
            accent
            label="Confidence"
            value={`${confidencePercent}%`}
          />
        </div>
      </div>
    </GlassCard>
  );
}

function AgentTimeline({ isSubmitting, processIndex, runState }) {
  return (
    <GlassCard className="p-5 sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <SectionHeader
          compact
          kicker="Agent activity timeline"
          title="Self-healing sequence"
        />
        <RefreshCw
          className={`h-5 w-5 text-slate-500 ${isSubmitting ? "animate-spin text-cyan-300" : ""}`}
          aria-hidden="true"
        />
      </div>

      <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {timelineItems.map((item, index) => {
          const status = getTimelineStatus(runState, processIndex, index);
          return (
            <TimelineStep
              item={item}
              key={item.label}
              status={status}
              step={index + 1}
            />
          );
        })}
      </ol>
    </GlassCard>
  );
}

function TimelineStep({ item, status, step }) {
  const Icon = item.icon;
  const isActive = status === "active";
  const isComplete = status === "complete";
  const styles = toneStyles[item.tone];
  const statusText = isActive ? "PROCESSING" : isComplete ? "DONE" : "QUEUED";

  return (
    <li
      className={`group relative min-h-36 overflow-hidden rounded-2xl border bg-slate-900/55 p-4 shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-400/40 ${
        isActive
          ? "border-cyan-400/40 shadow-cyan-500/10"
          : isComplete
            ? `border-slate-700/50 ${styles.glow}`
            : "border-slate-800/70 opacity-80"
      }`}
    >
      {isActive ? <span className="timeline-scan" aria-hidden="true" /> : null}
      <div className="relative flex items-start gap-3">
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border shadow-lg ${
            isActive || isComplete
              ? styles.icon
              : "border-slate-700/60 bg-slate-800/50 text-slate-500"
          }`}
        >
          {isActive ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          ) : (
            <Icon className="h-5 w-5" aria-hidden="true" />
          )}
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">
              Step {step}
            </p>
            <span
              className={`rounded-full border px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.16em] ${
                isActive || isComplete
                  ? styles.badge
                  : "border-slate-700 bg-slate-800/50 text-slate-500"
              }`}
            >
              {statusText}
            </span>
          </div>
          <p className="mt-3 text-sm font-bold text-slate-50">{item.label}</p>
          <p className="mt-2 text-sm leading-5 text-slate-400">{item.detail}</p>
        </div>
      </div>
    </li>
  );
}

function ManualTriggerPanel({
  error,
  form,
  isSubmitting,
  notice,
  onChange,
  onSubmit,
}) {
  return (
    <GlassCard className="p-5 sm:p-6 xl:sticky xl:top-6">
      <SectionHeader
        icon={TerminalSquare}
        kicker="Manual trigger"
        title="Heal a failed pipeline"
      />

      <form className="mt-6 grid gap-4" onSubmit={onSubmit}>
        <Field
          inputMode="numeric"
          label="project_id"
          onChange={(event) => onChange("projectId", event.target.value)}
          value={form.projectId}
        />
        <Field
          inputMode="numeric"
          label="pipeline_id"
          onChange={(event) => onChange("pipelineId", event.target.value)}
          value={form.pipelineId}
        />
        <Field
          label="ref"
          onChange={(event) => onChange("ref", event.target.value)}
          value={form.ref}
        />
        <Field
          label="demo token"
          onChange={(event) => onChange("demoToken", event.target.value)}
          type="password"
          value={form.demoToken}
        />

        <PrimaryButton isLoading={isSubmitting}>
          {isSubmitting ? "Healing pipeline..." : "Trigger healing"}
        </PrimaryButton>
      </form>

      {notice ? (
        <MessageBox icon={CheckCircle2} tone="info">
          {notice}
        </MessageBox>
      ) : null}

      {error ? (
        <MessageBox icon={AlertTriangle} tone="warning">
          {error}
        </MessageBox>
      ) : null}
    </GlassCard>
  );
}

function DiagnosisCard({ latestRun, confidencePercent }) {
  return (
    <GlassCard className="p-5">
      <SectionHeader
        compact
        icon={Brain}
        kicker="Diagnosis"
        title="Failure analysis"
      />
      <div className="mt-5 space-y-4">
        <InfoBlock label="Root cause" value={latestRun.rootCause} />
        <InfoBlock label="Error type" value={latestRun.errorType} />
        <div className="grid grid-cols-2 gap-3">
          <MetricCard compact label="Confidence" value={`${confidencePercent}%`} />
          <MetricCard compact accent label="Risk" value={latestRun.riskLevel} />
        </div>
      </div>
    </GlassCard>
  );
}

function FixPlanCard({ latestRun }) {
  return (
    <GlassCard className="p-5">
      <SectionHeader
        compact
        icon={ShieldCheck}
        kicker="Fix plan"
        title="Validated patch"
      />
      <div className="mt-5 space-y-4">
        <InfoBlock label="File modified" value={latestRun.sourceFilePath} mono />
        <InfoBlock label="Branch name" value={latestRun.branchName} mono />
        <InfoBlock label="Commit message" value={latestRun.commitMessage} />
      </div>
    </GlassCard>
  );
}

function MergeRequestCard({ latestRun }) {
  return (
    <GlassCard className="p-5">
      <SectionHeader
        compact
        icon={GitMerge}
        kicker="GitLab handoff"
        title="Review ready"
      />
      <div className="mt-5 grid gap-3">
        <ExternalButton href={latestRun.mrUrl} icon={GitMerge}>
          Open Merge Request
        </ExternalButton>
        <ExternalButton href={latestRun.pipelineUrl} icon={Activity} variant="light">
          View Pipeline
        </ExternalButton>
      </div>
      <div className="mt-5 rounded-2xl border border-slate-700/40 bg-slate-950/35 p-4">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">
          Policy
        </p>
        <p className="mt-2 text-sm font-medium leading-6 text-slate-300">
          SyntaxSentinel prepares fixes, but never merges automatically.
        </p>
      </div>
    </GlassCard>
  );
}

function GlassCard({ children, className = "" }) {
  return (
    <section
      className={`rounded-2xl border border-slate-700/40 bg-slate-900/60 shadow-2xl shadow-cyan-500/5 backdrop-blur-xl ${className}`}
    >
      {children}
    </section>
  );
}

function SectionHeader({ compact = false, icon: Icon, kicker, title }) {
  return (
    <div className="flex items-center gap-3">
      {Icon ? (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-700/60 bg-slate-950/40 text-cyan-200">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      ) : null}
      <div>
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">
          {kicker}
        </p>
        <h2
          className={`mt-1 font-black tracking-tight text-slate-50 ${
            compact ? "text-xl" : "text-3xl sm:text-4xl"
          }`}
        >
          {title}
        </h2>
      </div>
    </div>
  );
}

function StatusPill({ icon: Icon = Activity, label, status, variant = "default" }) {
  const online = variant === "online";

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-700/50 bg-slate-950/35 px-4 py-3">
      {online ? (
        <span className="agent-dot" aria-hidden="true" />
      ) : (
        <Icon className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
      )}
      <div className="min-w-0">
        <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">
          {label}
        </p>
        <p className="truncate text-sm font-bold text-slate-100">{status}</p>
      </div>
    </div>
  );
}

function TimestampPill({ value }) {
  return (
    <div className="inline-flex min-w-44 items-center gap-2 rounded-full border border-slate-700/50 bg-slate-950/35 px-4 py-2 text-sm font-semibold text-slate-300">
      <Clock3 className="h-4 w-4 text-slate-500" aria-hidden="true" />
      {value}
    </div>
  );
}

function MetricCard({ accent = false, compact = false, label, value }) {
  return (
    <div
      className={`bg-slate-900/65 p-4 ${
        accent ? "shadow-inner shadow-cyan-500/5" : ""
      }`}
    >
      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p
        className={`mt-2 break-words font-black tracking-tight ${
          compact ? "text-xl" : "text-2xl"
        } ${accent ? "text-cyan-200" : "text-slate-50"}`}
      >
        {value}
      </p>
    </div>
  );
}

function Field({ label, ...props }) {
  return (
    <label className="grid gap-2">
      <span className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">
        {label}
      </span>
      <input
        className="min-h-12 rounded-2xl border border-slate-700/55 bg-slate-950/35 px-4 text-sm font-semibold text-slate-100 transition-all placeholder:text-slate-600 focus:border-cyan-400/60 focus:bg-slate-950/55 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
        required
        {...props}
      />
    </label>
  );
}

function PrimaryButton({ children, isLoading }) {
  return (
    <button
      className="premium-button mt-1 inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-black text-white transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
      disabled={isLoading}
      type="submit"
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

function InfoBlock({ label, value, mono = false }) {
  return (
    <div>
      <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p
        className={`mt-2 rounded-2xl border border-slate-700/40 bg-slate-950/30 p-4 text-sm leading-6 text-slate-300 ${
          mono ? "font-mono" : "font-medium"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function MessageBox({ children, icon: Icon, tone }) {
  const styles =
    tone === "warning"
      ? "border-amber-400/25 bg-amber-400/10 text-amber-100"
      : "border-cyan-400/25 bg-cyan-400/10 text-cyan-100";

  return (
    <div className={`mt-4 flex gap-3 rounded-2xl border p-4 text-sm font-semibold ${styles}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

function ExternalButton({ href, icon: Icon, children, variant = "dark" }) {
  const styles =
    variant === "dark"
      ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-100 hover:border-cyan-300/60 hover:bg-cyan-400/15"
      : "border-slate-700/50 bg-slate-950/35 text-slate-200 hover:border-slate-500/70 hover:bg-slate-800/45";

  return (
    <a
      className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl border px-4 py-3 text-sm font-black transition-all hover:-translate-y-0.5 ${styles}`}
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

function getTimelineStatus(runState, processIndex, index) {
  if (runState === "running") {
    if (index < processIndex) return "complete";
    if (index === processIndex) return "active";
    return "queued";
  }

  if (runState === "error") {
    return index === 0 ? "active" : "queued";
  }

  return "complete";
}

export default App;
