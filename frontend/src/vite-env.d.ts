/// <reference types="vite/client" />

declare module 'lucide-react' {
  import * as React from 'react';
  export interface IconProps extends React.SVGProps<SVGSVGElement> {
    size?: number | string;
    color?: string;
    strokeWidth?: number | string;
  }
  export type Icon = React.FC<IconProps>;

  export const Sparkles: Icon;
  export const ArrowRight: Icon;
  export const ArrowLeft: Icon;
  export const CheckCircle2: Icon;
  export const CheckCircle: Icon;
  export const MessageSquare: Icon;
  export const Compass: Icon;
  export const Award: Icon;
  export const Send: Icon;
  export const AlertCircle: Icon;
  export const RotateCcw: Icon;
  export const Volume2: Icon;
  export const TrendingUp: Icon;
  export const Clock: Icon;
  export const AlertTriangle: Icon;
  export const BookOpen: Icon;
  export const Flame: Icon;
  export const RefreshCw: Icon;
  export const BarChart2: Icon;
  export const User: Icon;
  export const Users: Icon;
  export const UserCheck: Icon;
  export const Search: Icon;
  export const Calendar: Icon;
  export const ChevronRight: Icon;
  export const ChevronDown: Icon;
  export const Database: Icon;
  export const Cpu: Icon;
  export const Filter: Icon;
  export const ArrowUpRight: Icon;
  export const Info: Icon;
  export const X: Icon;
}
