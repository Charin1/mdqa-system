import React from 'react';

const variants = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
  outline: 'border border-muted-foreground hover:bg-muted',
  destructive: 'bg-destructive text-primary-foreground hover:bg-destructive/90',
};

const sizes = {
  md: 'px-4 py-2 text-sm',
  icon: 'h-10 w-10',
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

export const Button = ({ className, variant = 'primary', size = 'md', ...props }: ButtonProps) => {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    />
  );
};