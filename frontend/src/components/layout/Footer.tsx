import { Link } from 'react-router-dom';

export const Footer = () => {
  return (
    <footer className="border-t border-border mt-16 pt-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
          <div className="text-center sm:text-left">
            <p className="text-sm text-text-secondary">
              &copy; {new Date().getFullYear()} SYQ Intelligence Platform. All rights reserved.
            </p>
          </div>
          <div className="flex space-x-4 mt-4 sm:mt-0">
            <Link to="/" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              About
            </Link>
            <Link to="/privacy" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Privacy
            </Link>
            <Link to="/terms" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Terms
            </Link>
            <Link to="/contact" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Contact
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};