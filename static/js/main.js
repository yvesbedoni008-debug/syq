// SYQ Enhanced JavaScript
// Adds interactivity and enhanced UI elements

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();

    // Initialize animated counters
    initAnimatedCounters();

    // Add hover effects to cards
    initCardHoverEffects();

    // Initialize scroll animations
    initScrollAnimations();

    // Add pulse animation to accent elements
    initPulseAnimation();
});

// Initialize tooltips for elements with title attribute
function initTooltips() {
    const elements = document.querySelectorAll('[title]');
    elements.forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.innerHTML = this.title;
            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${window.scrollY + rect.top - 10}px`;
            tooltip.style.left = `${window.scrollX + rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;

            // Add slight delay for animation
            setTimeout(() => tooltip.style.opacity = '1', 10);
        });

        el.addEventListener('mouseleave', function() {
            const tooltips = document.querySelectorAll('.tooltip');
            tooltips.forEach(t => t.remove());
        });
    });
}

// Initialize animated counters for stats
function initAnimatedCounters() {
    // This would be used if we had stats sections with numbers that animate up
    // For now, we'll prepare the function for future use
}

// Add hover effects to card-like elements
function initCardHoverEffects() {
    const cards = document.querySelectorAll('.highlight, .callout');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
}

// Initialize scroll-based animations
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.fade-in');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Uncomment if you want to animate only once
                // observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '-50px'
    });

    animatedElements.forEach(el => observer.observe(el));
}

// Add pulse animation to accent elements
function initPulseAnimation() {
    const accents = document.querySelectorAll('.accent, .btn-accent');
    accents.forEach(accent => {
        accent.style.setProperty('--pulse-color', 'rgba(182, 255, 59, 0.3)');
    });
}

// Add ripple effect to buttons
function initButtonRipple() {
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);

            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            ripple.className = 'ripple';

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Initialize ripple effect after DOM loads
document.addEventListener('DOMContentLoaded', initButtonRipple);

// Add CSS for ripple effect dynamically
function addRippleCSS() {
    const style = document.createElement('style');
    style.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        .ripple {
            position: absolute;
            background: radial-gradient(circle, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        }
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }

        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.875rem;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            white-space: nowrap;
        }

        /* Pulse animation for accent elements */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(182, 255, 59, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(182, 255, 59, 0); }
            100% { box-shadow: 0 0 0 0 rgba(182, 255, 59, 0); }
        }

        .pulse-animated {
            animation: pulse 2s infinite;
        }
    `;
    document.head.appendChild(style);
}

// Add the CSS when DOM loads
document.addEventListener('DOMContentLoaded', addRippleCSS);

// Add some demo data visualization would go here if we had charting libraries
// For now, we'll add a simple function that could be extended
function initDemoVisualizations() {
    // This would initialize charts/graphs if we added a charting library
    // For example, if we added Chart.js or similar
}

// Apply pulse animation to some elements for visual interest
function applyPulseToElements() {
    const pulseElements = document.querySelectorAll('.accent');
    pulseElements.forEach((el, index) => {
        // Stagger the animations
        el.style.animationDelay = `${index * 0.5}s`;
        el.classList.add('pulse-animated');
    });
}

// Call this after a brief delay to let initial animations complete
setTimeout(applyPulseToElements, 1000);

// Add functionality to the buttons
document.addEventListener('DOMContentLoaded', function() {
    const githubBtn = document.querySelector('.btn-accent');
    const docsBtn = document.querySelector('.btn-outline');

    if (githubBtn) {
        githubBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // In a real app, this would go to GitHub
            alert('Redirecting to GitHub repository...');
            // window.location.href = '/github'; // Uncomment for real implementation
        });
    }

    if (docsBtn) {
        docsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // In a real app, this would go to docs
            alert('Opening documentation...');
            // window.location.href = '/docs'; // Uncomment for real implementation
        });
    }
});

// Add a simple notification system
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            ${message}
        </div>
        <button class="notification-close">&times;</button>
    `;

    document.body.appendChild(notification);

    // Add CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #fff;
            border-left: 4px solid;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
            z-index: 1000;
        }

        .notification-info { border-color: #B6FF3B; }
        .notification-success { border-color: #4CAF50; }
        .notification-warning { border-color: #FF9800; }
        .notification-error { border-color: #F44336; }

        .notification-content {
            padding: 12px 16px;
            flex: 1;
            font-size: 0.9rem;
            color: #333;
        }

        .notification-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0 8px;
            color: #666;
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .notification.hide {
            animation: slideOut 0.3s ease-in forwards;
        }

        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Add close functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', function() {
        notification.classList.add('hide');
        setTimeout(() => notification.remove(), 300);
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Example usage - uncomment to test
// setTimeout(() => showNotification('Welcome to SYQ Opportunity Intelligence Platform!', 'success'), 2000);

// Add some dynamic content based on time of day
function updateDynamicContent() {
    const hour = new Date().getHours();
    let greeting = '';

    if (hour < 12) {
        greeting = 'Good morning';
    } else if (hour < 18) {
        greeting = 'Good afternoon';
    } else {
        greeting = 'Good evening';
    }

    // We could update a greeting element if we had one
    // For now, just log it for demonstration
    console.log(`${greeting}! Welcome to SYQ.`);
}

// Call when page loads
document.addEventListener('DOMContentLoaded', updateDynamicContent);