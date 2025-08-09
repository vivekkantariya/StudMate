document.addEventListener('DOMContentLoaded', function () {
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');

    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        const mobileIcon = mobileThemeToggle ? mobileThemeToggle.querySelector('i') : null;

        // Check for saved theme preference or use preferred color scheme
        const savedTheme = localStorage.getItem('theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

        // Apply the saved theme
        if (savedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            if (mobileIcon) {
                mobileIcon.classList.remove('fa-moon');
                mobileIcon.classList.add('fa-sun');
            }
            if (mobileThemeToggle) {
                mobileThemeToggle.querySelector('span').textContent = 'Light Mode';
            }
        }

        // Toggle theme function
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');

            if (currentTheme === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                if (mobileIcon) {
                    mobileIcon.classList.remove('fa-sun');
                    mobileIcon.classList.add('fa-moon');
                }
                if (mobileThemeToggle) {
                    mobileThemeToggle.querySelector('span').textContent = 'Dark Mode';
                }
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                if (mobileIcon) {
                    mobileIcon.classList.remove('fa-moon');
                    mobileIcon.classList.add('fa-sun');
                }
                if (mobileThemeToggle) {
                    mobileThemeToggle.querySelector('span').textContent = 'Light Mode';
                }
                localStorage.setItem('theme', 'dark');
            }
        }

        // Desktop theme toggle
        themeToggle.addEventListener('click', toggleTheme);

        // Mobile theme toggle
        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', toggleTheme);
        }
    }

    // Sidebar toggle functionality
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Toggle sidebar collapse/expand (desktop only)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('collapsed');

            // Change icon based on state
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        });
    }

    // Mobile menu toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('show');
            }
        });
    }

    // Close sidebar when clicking overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (event) {
        if (window.innerWidth <= 992 &&
            sidebar.classList.contains('show') &&
            !sidebar.contains(event.target) &&
            event.target !== mobileMenuBtn &&
            !mobileMenuBtn.contains(event.target)) {
            sidebar.classList.remove('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('show');
            }
        }
    });

    // Close sidebar when window is resized to desktop
    window.addEventListener('resize', function () {
        if (window.innerWidth > 992) {
            sidebar.classList.remove('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('show');
            }
        }
    });

    // Notification button functionality
    const notificationBtn = document.getElementById('notificationBtn');
    const mobileNotificationBtn = document.getElementById('mobileNotificationBtn');

    function handleNotification() {
        // Implement notification dropdown
        alert('Notification dropdown would open here');
    }

    if (notificationBtn) {
        notificationBtn.addEventListener('click', handleNotification);
    }

    if (mobileNotificationBtn) {
        mobileNotificationBtn.addEventListener('click', function () {
            handleNotification();
            // Close mobile sidebar after action
            if (window.innerWidth <= 992) {
                sidebar.classList.remove('show');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('show');
                }
            }
        });
    }

    // Close sidebar when clicking on mobile actions
    const mobileActions = document.querySelectorAll('.mobile-action-item');
    mobileActions.forEach(function (item) {
        item.addEventListener('click', function () {
            // Only close if it's not the theme toggle or notification button
            if (!this.id.includes('Theme') && !this.id.includes('Notification')) {
                if (window.innerWidth <= 992) {
                    setTimeout(function () {
                        sidebar.classList.remove('show');
                        if (sidebarOverlay) {
                            sidebarOverlay.classList.remove('show');
                        }
                    }, 100);
                }
            }
        });
    });

    // Handle escape key to close mobile sidebar
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && window.innerWidth <= 992 && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('show');
            }
        }
    });

    // Prevent sidebar from staying open when navigating via sidebar links
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 992) {
                setTimeout(function () {
                    sidebar.classList.remove('show');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('show');
                    }
                }, 100);
            }
        });
    });
});
