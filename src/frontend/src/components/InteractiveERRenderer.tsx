import React, { useEffect, useRef, useState, useCallback } from 'react';

interface InteractiveERRendererProps {
  chart: string;
  className?: string;
}

export const InteractiveERRenderer: React.FC<InteractiveERRendererProps> = ({ chart, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgContainerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGElement | null>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(true);

  // 使用 ref 存储最新的 scale 和 position，避免闭包问题
  const scaleRef = useRef(scale);
  const positionRef = useRef(position);

  useEffect(() => {
    scaleRef.current = scale;
  }, [scale]);

  useEffect(() => {
    positionRef.current = position;
  }, [position]);

  useEffect(() => {
    if (!chart || !svgContainerRef.current) return;

    setIsLoading(true);

    const renderER = async () => {
      // 创建离屏渲染容器，避免 mermaid 在 body 中创建临时元素导致抖动
      const offscreenContainer = document.createElement('div');
      offscreenContainer.style.cssText = 'position: fixed; left: -9999px; top: -9999px; visibility: hidden; pointer-events: none;';
      document.body.appendChild(offscreenContainer);

      try {
        // 修复格式问题
        let fixedChart = chart.trim();
        if (fixedChart.includes('}}%% erDiagram')) {
          fixedChart = fixedChart.replace('}}%% erDiagram', '}}%%\nerDiagram');
        }

        // 动态导入 mermaid
        const mermaid = (await import('mermaid')).default;

        // 优化的初始化配置
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          er: {
            diagramPadding: 30,
            layoutDirection: 'TB',
            minEntityWidth: 150,
            minEntityHeight: 100,
            entityPadding: 25,
            stroke: '#333',
            fill: '#f8f9fa',
            fontSize: 16,
            useMaxWidth: false
          }
        });

        // 在离屏容器中渲染
        const id = `interactive-er-${Date.now()}`;
        const result = await mermaid.render(id, fixedChart, offscreenContainer);

        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = result.svg;

          // 获取 SVG 元素
          const svg = svgContainerRef.current.querySelector('svg');
          if (svg) {
            svgRef.current = svg;

            // 设置 SVG 样式
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.cursor = 'grab';
            svg.style.userSelect = 'none';

            // 确保有 viewBox
            if (!svg.getAttribute('viewBox')) {
              try {
                const bbox = svg.getBBox();
                svg.setAttribute('viewBox', `0 0 ${bbox.width + 60} ${bbox.height + 60}`);
              } catch (e) {
                svg.setAttribute('viewBox', '0 0 800 600');
              }
            }

            // 重置缩放和位置
            setScale(1);
            setPosition({ x: 0, y: 0 });
            updateTransform(svg, 1, { x: 0, y: 0 });
          }

          console.log('✅ 交互式 ER 图渲染完成！');
          setIsLoading(false);
        }
      } catch (error) {
        console.error('❌ ER图渲染失败:', error);
        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = `
            <div style="padding: 20px; color: red; border: 1px solid red; border-radius: 8px; background: #ffe6e6;">
              <h3>渲染失败</h3>
              <p>${error}</p>
            </div>
          `;
        }
        setIsLoading(false);
      } finally {
        // 清理离屏容器
        if (offscreenContainer.parentNode) {
          offscreenContainer.parentNode.removeChild(offscreenContainer);
        }
      }
    };

    renderER();
  }, [chart]);

  // 更新变换
  const updateTransform = useCallback((svg: SVGElement, newScale: number, newPosition: { x: number, y: number }) => {
    svg.style.transform = `translate(${newPosition.x}px, ${newPosition.y}px) scale(${newScale})`;
    svg.style.transformOrigin = 'center center';
  }, []);

  // 使用 useEffect 添加 non-passive wheel 事件监听器，解决 preventDefault 警告
  useEffect(() => {
    const container = svgContainerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (!svgRef.current || !svgContainerRef.current) return;

      // 获取容器边界
      const containerRect = svgContainerRef.current.getBoundingClientRect();
      const mouseX = e.clientX;
      const mouseY = e.clientY;

      // 检查鼠标是否在ER图容器内
      const isMouseInContainer = (
        mouseX >= containerRect.left &&
        mouseX <= containerRect.right &&
        mouseY >= containerRect.top &&
        mouseY <= containerRect.bottom
      );

      // 只有当鼠标在ER图容器内时才进行缩放，否则允许正常滚动
      if (!isMouseInContainer) {
        return;
      }

      // 阻止默认滚动行为并停止事件冒泡
      e.preventDefault();
      e.stopPropagation();

      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const currentScale = scaleRef.current;
      const currentPosition = positionRef.current;
      const newScale = Math.max(0.2, Math.min(3, currentScale * delta));

      setScale(newScale);
      updateTransform(svgRef.current, newScale, currentPosition);
    };

    // 添加 non-passive 事件监听器
    container.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      container.removeEventListener('wheel', handleWheel);
    };
  }, [updateTransform]);

  // 开始拖动 - 只在鼠标在ER图区域内时生效
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!svgRef.current || !svgContainerRef.current) return;

    // 获取容器边界
    const containerRect = svgContainerRef.current.getBoundingClientRect();
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    // 检查鼠标是否在ER图容器内
    const isMouseInContainer = (
      mouseX >= containerRect.left &&
      mouseX <= containerRect.right &&
      mouseY >= containerRect.top &&
      mouseY <= containerRect.bottom
    );

    if (!isMouseInContainer) {
      return;
    }

    // 阻止事件冒泡，避免影响外部元素
    e.stopPropagation();

    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    svgRef.current.style.cursor = 'grabbing';
  };

  // 拖动中 - 添加边界检查
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !svgRef.current) return;

    // 阻止事件冒泡
    e.stopPropagation();

    const newPosition = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    };

    setPosition(newPosition);
    updateTransform(svgRef.current, scale, newPosition);
  };

  // 结束拖动 - 添加事件处理
  const handleMouseUp = (e?: React.MouseEvent) => {
    if (!svgRef.current) return;

    // 如果有事件对象，阻止冒泡
    if (e) {
      e.stopPropagation();
    }

    setIsDragging(false);
    svgRef.current.style.cursor = 'grab';
  };

  // 重置视图
  const resetView = () => {
    if (!svgRef.current) return;

    const newScale = 1;
    const newPosition = { x: 0, y: 0 };

    setScale(newScale);
    setPosition(newPosition);
    updateTransform(svgRef.current, newScale, newPosition);
  };

  return (
    <div className={className} style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* 控制按钮 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 10,
        display: 'flex',
        gap: '5px',
        opacity: isLoading ? 0 : 1,
        transition: 'opacity 0.2s ease-in-out'
      }}>
        <button
          onClick={() => {
            if (!svgRef.current) return;
            const newScale = Math.max(0.2, scale * 0.8);
            setScale(newScale);
            updateTransform(svgRef.current, newScale, position);
          }}
          style={{
            padding: '5px 10px',
            background: 'rgba(255,255,255,0.9)',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
          title="缩小"
        >
          −
        </button>
        <button
          onClick={resetView}
          style={{
            padding: '5px 10px',
            background: 'rgba(255,255,255,0.9)',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
          title="重置视图"
        >
          ⌂
        </button>
        <button
          onClick={() => {
            if (!svgRef.current) return;
            const newScale = Math.min(3, scale * 1.25);
            setScale(newScale);
            updateTransform(svgRef.current, newScale, position);
          }}
          style={{
            padding: '5px 10px',
            background: 'rgba(255,255,255,0.9)',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
          title="放大"
        >
          +
        </button>
      </div>

      {/* 缩放信息 */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        left: '10px',
        zIndex: 10,
        padding: '5px 10px',
        background: 'rgba(0,0,0,0.7)',
        color: 'white',
        borderRadius: '4px',
        fontSize: '12px',
        opacity: isLoading ? 0 : 1,
        transition: 'opacity 0.2s ease-in-out'
      }}>
        {Math.round(scale * 100)}%
      </div>

      {/* 外层容器 - 固定尺寸，防止抖动 */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '300px',
          border: '1px solid #e0e0e0',
          background: 'white',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          position: 'relative'
        }}
      >
        {/* 加载状态 - 绝对定位，不影响布局 */}
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: '16px',
          background: 'white',
          opacity: isLoading ? 1 : 0,
          visibility: isLoading ? 'visible' : 'hidden',
          transition: 'opacity 0.2s ease-in-out',
          zIndex: 5
        }}>
          <div>
            <div style={{
              width: '40px',
              height: '40px',
              border: '3px solid #f3f3f3',
              borderTop: '3px solid #3498db',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 15px'
            }}></div>
            正在渲染交互式 ER 图...
          </div>
        </div>

        {/* SVG 容器 - 绝对定位，渲染完成后显示 */}
        <div
          ref={svgContainerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={(e) => handleMouseUp(e)}
          onMouseLeave={() => handleMouseUp()}
          style={{
            position: 'absolute',
            inset: 0,
            touchAction: 'none',
            opacity: isLoading ? 0 : 1,
            visibility: isLoading ? 'hidden' : 'visible',
            transition: 'opacity 0.2s ease-in-out'
          }}
        />

        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
};

export default InteractiveERRenderer;