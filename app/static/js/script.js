// Superhuman Frontend Bootstrap
document.addEventListener('DOMContentLoaded', () => {
    console.log('Superhuman Frontend Loaded');
    const root = document.getElementById('root');
    if (root) {
        root.dataset.status = 'loaded';
    }
});
