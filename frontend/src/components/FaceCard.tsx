type FaceCardProps = {
  name: string;
  stateLabel: string;
  currentReply: string;
};

export function FaceCard({ name, stateLabel, currentReply }: FaceCardProps) {
  return (
    <section className="face-card">
      <div className="face-card__bubble">
        <div className="face-card__ears" />
        <div className="face-card__face">
          <span className="face-card__eye" />
          <span className="face-card__eye" />
          <span className="face-card__nose" />
        </div>
      </div>
      <p className="eyebrow">{stateLabel}</p>
      <h1>{name}</h1>
      <p className="reply-chip">{currentReply || "ここで、おはなしをきくよ。"}</p>
    </section>
  );
}

