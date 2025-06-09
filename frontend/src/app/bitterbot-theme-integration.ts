// BitterBot Theme Integration Script

export function initBitterBotTheme() {
  // Add theme class to body
  if (typeof document !== 'undefined') {
    document.body.classList.add('bitterbot-theme');
    
    // Replace "Bitterbot" text with "BitterBot" throughout the dashboard
    const replaceBitterbotText = () => {
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            if (node.nodeValue?.includes('Bitterbot')) {
              return NodeFilter.FILTER_ACCEPT;
            }
            return NodeFilter.FILTER_SKIP;
          }
        }
      );

      const nodesToReplace: Text[] = [];
      let node;
      while (node = walker.nextNode()) {
        nodesToReplace.push(node as Text);
      }

      nodesToReplace.forEach(node => {
        if (node.nodeValue) {
          node.nodeValue = node.nodeValue.replace(/Bitterbot/g, 'BitterBot');
        }
      });
    };

    // Replace text on initial load
    replaceBitterbotText();

    // Watch for dynamic content changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          replaceBitterbotText();
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Add purple particles effect
    const createParticles = () => {
      const particlesContainer = document.createElement('div');
      particlesContainer.className = 'bitterbot-particles';
      particlesContainer.style.cssText = `
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
      `;

      for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
          position: absolute;
          width: 4px;
          height: 4px;
          background: rgba(168, 85, 247, 0.6);
          border-radius: 50%;
          left: ${Math.random() * 100}%;
          animation: float ${20 + Math.random() * 10}s linear infinite;
          animation-delay: ${Math.random() * 20}s;
        `;
        particlesContainer.appendChild(particle);
      }

      document.body.appendChild(particlesContainer);
    };

    // Add particles after a slight delay to ensure DOM is ready
    setTimeout(createParticles, 100);

    // Update favicon to purple
    const updateFavicon = () => {
      const link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
      if (link) {
        // Create a purple-tinted favicon using canvas
        const canvas = document.createElement('canvas');
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');
        
        if (ctx) {
          // Draw purple gradient circle
          const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
          gradient.addColorStop(0, '#a855f7');
          gradient.addColorStop(1, '#7c3aed');
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(16, 16, 14, 0, Math.PI * 2);
          ctx.fill();
          
          // Draw "BB" text
          ctx.fillStyle = 'white';
          ctx.font = 'bold 14px sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('BB', 16, 16);
          
          link.href = canvas.toDataURL();
        }
      }
    };

    updateFavicon();

    // Clean up on unmount
    return () => {
      document.body.classList.remove('bitterbot-theme');
      observer.disconnect();
      const particles = document.querySelector('.bitterbot-particles');
      if (particles) {
        particles.remove();
      }
    };
  }
}