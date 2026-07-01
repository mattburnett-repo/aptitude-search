type PipelineActionsProps = {
  loading: boolean;
  canRun: boolean;
  onRun: () => void;
  inline?: boolean;
};

export function PipelineActions({
  loading,
  canRun,
  onRun,
  inline = false,
}: PipelineActionsProps) {
  const button = (
    <button
      type="button"
      className="primary-cta"
      disabled={loading || !canRun}
      onClick={onRun}
    >
      {loading ? "Running…" : "Go →"}
    </button>
  );

  if (inline) {
    return button;
  }

  return <div className="actions actions-primary">{button}</div>;
}
