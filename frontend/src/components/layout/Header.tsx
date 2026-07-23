import { Link } from 'react-router-dom';
import { Menu, MenuItem, CommandKCommand, CommandKProvider, CommandKInput, CommandKList, CommandH1, CommandEmpty, CommandDivider, CommandItem, CommandGroup, CommandPrompt } from '@headlessui/react';
import { Search, Menu as MenuIcon, Sun, Moon, LogOut } from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Check localStorage or system preference
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Update HTML class for tailwind dark mode
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    // In a real app, this would trigger search/filter
  };

  const handleLogout = () => {
    // Implement logout logic
    console.log('Logging out');
  };

  return (
    <header className="border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex-shrink-0 flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <span className="h-8 w-8 flex items-center justify-center bg-accent/10 rounded-lg text-accent">
                SYQ
              </span>
              <span className="text-xl font-semibold tracking-tight text-text-primary">
                SYQ Intelligence
              </span>
            </Link>
          </div>
          <div className="flex-1 flex items-center justify-center sm:hidden">
            {/* Mobile search button */}
            <button type="button" className="rounded-md p-2 text-text-secondary hover:text-text-primary hover:bg-muted">
              <Search className="h-5 w-5" />
            </button>
          </div>
          <div className="flex items-center space-x-4">
            {/* Search - visible on desktop */}
            <div className="hidden sm:block">
              <label className="sr-only" htmlFor="search">
                Search opportunities
              </label>
              <div className="relative w-64">
                <div className="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
                  <Search className="h-5 w-5 text-text-secondary" />
                </div>
                <input
                  id="search"
                  type="text"
                  className="block w-full pl-10 pr-3 py-2 text-base font-normal text-text-primary bg-background/70 border-border rounded-md placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-accent focus:bg-background transition-colors"
                  placeholder="Search opportunities..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                />
              </div>
            </div>

            {/* Theme toggle */}
            <button
              type="button"
              className="p-2 rounded-full hover:bg-muted/50 transition-colors duration-200"
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <Sun className="h-5 w-5 text-yellow-400" />
              ) : (
                <Moon className="h-5 w-5 text-gray-400" />
              )}
            </button>

            {/* User menu */}
            <div className="relative">
              <div>
                <button
                  type="button"
                  className="flex items-center space-x-2 rounded-full p-1 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-muted"
                  aria-haspopup="true"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <span className="sr-only">View user profile</span>
                  <span className="flex items-center space-x-1">
                    {/* Placeholder for user avatar */}
                    <div className="h-8 w-8 flex items-center justify-center bg-accent/20 rounded-full text-accent">
                      J
                    </div>
                    <span className="hidden md:block">
                      John Doe
                    </span>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="w-4 h-4 opacity-50 transition-transform duration-200"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="m19.5 8.25-5.7 5.7-5.7-5.7"
                      />
                    </svg>
                  </span>
                </button>
              </div>
              {/* Dropdown menu */}
              {userMenuOpen && (
                <Menu className="z-50 mt-2 w-56 origin-top-right right-0">
                  <div className="px-1 pt-1 pb-2 bg-background/95 backdrop-blur-sm border border-border rounded-md shadow-lg">
                    <MenuItem>
                      {/* Profile link */}
                      <a href="#" className="block px-4 py-2 text-sm text-text-primary hover:bg-accent/10">
                        Your Profile
                      </a>
                    </MenuItem>
                    <MenuItem>
                      {/* Settings link */}
                      <a href="#" className="block px-4 py-2 text-sm text-text-primary hover:bg-accent/10">
                        Settings
                      </a>
                    </MenuItem>
                    <MenuItem>
                      {/* Feedback link */}
                      <a href="/feedback" className="block px-4 py-2 text-sm text-text-primary hover:bg-accent/10">
                        Feedback
                      </a>
                    </MenuItem>
                    <Divider className="my-1" />
                    <MenuItem>
                      <button type="button"
                              className="block w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-accent/10"
                              onClick={handleLogout}>
                        Sign out
                      </button>
                    </MenuItem>
                  </div>
                </Menu>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Simple divider
const Divider = ({ className }: { className?: string }) => (
  <hr className={`border-t border-border/50 ${className}`} />
);