'use client';

interface BitterBotAvatarProps {
  size?: number;
  variant?: 'circle' | 'brain';
}

export function BitterBotAvatar({ size = 32, variant = 'brain' }: BitterBotAvatarProps) {
  if (variant === 'brain') {
    return (
      <div 
        className="bb-avatar flex items-center justify-center"
        style={{ fontSize: size * 0.7 }}
      >
        <span className="brain-icon">🧠</span>
      </div>
    );
  }

  // Circle variant with BB text
  return (
    <div 
      className="bb-avatar-circle flex items-center justify-center"
      style={{
        width: size,
        height: size,
        background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
        borderRadius: '50%',
        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)',
      }}
    >
      <span 
        className="bb-text text-white font-bold"
        style={{ fontSize: size * 0.4 }}
      >
        BB
      </span>
    </div>
  );
}