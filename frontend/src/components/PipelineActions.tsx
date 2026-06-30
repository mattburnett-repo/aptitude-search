type PipelineActionsProps = {
  loading: boolean;
  canRun: boolean;
  onRun: () => void;
};

export function PipelineActions({
  loading,
  canRun,
  onRun,
}: PipelineActionsProps) {
  return (
    <div className="actions actions-primary">
      <button
        type="button"
        className="primary-cta"
        disabled={loading || !canRun}
        onClick={onRun}
      >
        {loading ? "Running…" : "Go →"}
      </button>
    </div>
  );
}
