import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen bg-background overflow-hidden text-foreground">
      <Sidebar />
      <main className="flex-1 flex flex-col p-4 md:p-8 overflow-hidden">
        <div className="flex-1 min-h-0 mx-auto max-w-7xl w-full">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;