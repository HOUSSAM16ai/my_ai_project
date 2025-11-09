declare module 'react-katex' {
  import * as React from 'react';
  export interface KatexProps {
    children?: React.ReactNode;
    math?: string;
    errorColor?: string;
    renderError?: (error: Error) => React.ReactNode;
  }
  export const InlineMath: React.FC<KatexProps>;
  export const BlockMath: React.FC<KatexProps>;
}
