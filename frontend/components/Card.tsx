import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  badge,
  action,
  children,
  className = '',
}) => {
  return (
    <div
      className={`rounded-xl border border-gray-800 bg-[#121826] p-5 shadow-lg transition-colors hover:border-gray-700/60 ${className}`}
    >
      {(title || subtitle || badge || action) && (
        <div className="mb-4 flex items-center justify-between border-b border-gray-800/60 pb-3">
          <div>
            <div className="flex items-center gap-2">
              {title && <h3 className="text-base font-semibold text-gray-100">{title}</h3>}
              {badge}
            </div>
            {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
