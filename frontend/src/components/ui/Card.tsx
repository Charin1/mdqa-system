import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const Card = ({ className, children, ...props }: CardProps) => {
  return (
    <div
      className={`bg-card text-card-foreground border border-muted rounded-lg shadow-lg ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};