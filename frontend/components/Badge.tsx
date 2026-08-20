import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'green' | 'red' | 'amber' | 'blue' | 'purple' | 'gray';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'gray',
  size = 'md',
}) => {
  const variantStyles = {
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    gray: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border ${variantStyles[variant]} ${sizeStyles[size]}`}
    >
      {children}
    </span>
  );
};
