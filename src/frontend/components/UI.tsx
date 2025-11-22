import React, { ReactNode } from 'react';
import { Check } from 'lucide-react';

// --- Button ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'default' | 'dashed' | 'text' | 'danger';
  icon?: ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ children, variant = 'default', className = '', icon, ...props }) => {
  const baseStyles = "inline-flex items-center justify-center px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-primary text-white hover:bg-primary-hover border border-transparent focus:ring-blue-500",
    default: "bg-white text-gray-700 border border-gray-300 hover:text-primary hover:border-primary focus:ring-gray-200",
    dashed: "bg-white text-gray-700 border border-dashed border-gray-300 hover:text-primary hover:border-primary",
    text: "bg-transparent text-gray-700 shadow-none hover:bg-gray-100 border-none",
    danger: "bg-white text-error border border-error hover:bg-red-50 focus:ring-red-200"
  };

  return (
    <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};

// --- Input ---
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input: React.FC<InputProps> = ({ label, className = '', ...props }) => (
  <div className="flex flex-col gap-1.5">
    {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
    <input 
      className={`px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all shadow-sm ${className}`}
      {...props} 
    />
  </div>
);

// --- Card ---
export const Card: React.FC<{ children: ReactNode; title?: ReactNode; extra?: ReactNode; className?: string }> = ({ children, title, extra, className = '' }) => (
  <div className={`bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:shadow-md ${className}`}>
    {(title || extra) && (
      <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/30 rounded-t-xl">
        <div className="font-semibold text-gray-800 text-base">{title}</div>
        <div>{extra}</div>
      </div>
    )}
    <div className="p-6">{children}</div>
  </div>
);

// --- Tag ---
export const Tag: React.FC<{ color?: 'blue' | 'green' | 'red' | 'orange' | 'gray'; children: ReactNode }> = ({ color = 'blue', children }) => {
  const colors = {
    blue: "bg-blue-50 text-blue-600 border-blue-200",
    green: "bg-green-50 text-green-600 border-green-200",
    red: "bg-red-50 text-red-600 border-red-200",
    orange: "bg-orange-50 text-orange-600 border-orange-200",
    gray: "bg-gray-50 text-gray-600 border-gray-200",
  };
  return (
    <span className={`inline-block px-2.5 py-0.5 text-xs font-medium border rounded-full ${colors[color]}`}>
      {children}
    </span>
  );
};

// --- ProgressBar ---
export const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => {
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden shadow-inner">
      <div 
        className="bg-primary h-full rounded-full transition-all duration-700 ease-out shadow-sm relative overflow-hidden" 
        style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
      >
        <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
      </div>
    </div>
  );
};

// --- Steps ---
interface StepItem {
  title: string;
  description?: string;
}
export const Steps: React.FC<{ steps: StepItem[]; current: number }> = ({ steps, current }) => {
  return (
    <div className="flex w-full items-center justify-between px-4">
      {steps.map((step, index) => {
        const isCompleted = index < current;
        const isCurrent = index === current;

        return (
          <div key={index} className="flex flex-col items-center relative flex-1 group">
            {/* Connector Line */}
            {index !== 0 && (
               <div className="absolute top-5 right-[50%] w-full h-[2px] -z-10">
                 <div className={`h-full transition-colors duration-500 ${index <= current ? 'bg-primary' : 'bg-gray-200'}`}></div>
               </div>
            )}
            
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-500 z-10 border-2 shadow-sm ${
              isCompleted ? 'bg-primary border-primary text-white' : 
              isCurrent ? 'bg-white border-primary text-primary ring-4 ring-blue-50 scale-110' : 
              'bg-white border-gray-200 text-gray-400'
            }`}>
              {isCompleted ? <Check size={18} strokeWidth={3} /> : index + 1}
            </div>
            <div className={`mt-3 text-sm font-medium transition-colors duration-300 ${
              isCurrent ? 'text-primary' : 
              isCompleted ? 'text-gray-800' : 
              'text-gray-400'
            }`}>
              {step.title}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// --- Modal ---
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  maxWidth?: string; // e.g. 'max-w-2xl'
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer, maxWidth = 'max-w-md' }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4 transition-opacity duration-300">
      <div className={`bg-white rounded-xl shadow-2xl w-full ${maxWidth} animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh] overflow-hidden`}>
        <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center shrink-0 bg-white">
          <h3 className="text-lg font-bold text-gray-800 tracking-tight">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors bg-gray-50 hover:bg-gray-100 p-1 rounded-full">
            <span className="sr-only">Close</span>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-8 overflow-y-auto bg-white">
          {children}
        </div>
        {footer && (
          <div className="px-8 py-5 bg-gray-50 border-t border-gray-100 flex justify-end gap-3 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};