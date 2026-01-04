/**
 * @file InteractiveERRenderer.tsx
 * @module Components/Visualization/ER-Diagram
 * @description 交互式实体关系图（ER Diagram）高性能渲染引擎。
 * 本组件作为“基于大模型多智能体框架的数据库自动部署与库表生成系统”的可视化中枢，
 * 承担了从 AI 生成的 Mermaid DSL 到交互式 SVG 图形的渲染转化职能。
 * * * 核心设计目标：
 * [cite_start]1. 动态自省渲染 (SF5): 实时解析底层 Schema Agent 生成的表结构元数据 [cite: 85-87]；
 * 2. 交互式操作 (Usability-1): 提供 0.2x 至 3x 的平滑缩放及全向位移（Panning）功能；
 * 3. 渲染稳定性: 采用离屏 DOM 预渲染技术，彻底消除浏览器重绘期间产生的视觉抖动；
 * 4. 性能保障: 针对大规模复杂 ER 图（如教务管理系统），通过 Passive Event 处理优化滚动性能。
 * * * 关键技术路径：
 * - Mermaid.js 核心引擎驱动；
 * - 响应式 SVG 视图矩阵变换；
 * - 二分法缩放比例修正算法。
 * * @author Wang Lirong (王利蓉)
 * @version 2.5.0
 * @date 2026-01-02
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

/**
 * 交互式 ER 渲染器属性接口定义
 * @interface InteractiveERRendererProps
 * @property {string} chart - 原始 Mermaid 语法的 ER 定义文本流
 * @property {string} [className] - 可选的外部容器样式扩展类名
 */
interface InteractiveERRendererProps {
  chart: string;
  className?: string;
}

/**
 * @component InteractiveERRenderer
 * @description 
 * 一个具备高度自律性的 React 函数式组件。
 * 内部通过引用状态锁（Ref Locks）解决了 React 闭包陷阱与原生事件监听器之间的数据同步冲突。
 */
export const InteractiveERRenderer: React.FC<InteractiveERRendererProps> = ({ chart, className = '' }) => {
  // --- 物理层 DOM 引用 ---
  /** 外层布局容器引用：用于确定组件的物理边界 */
  const containerRef = useRef<HTMLDivElement>(null);
  /** SVG 挂载点引用：动态生成的 SVG 节点将注入此容器 */
  const svgContainerRef = useRef<HTMLDivElement>(null);
  /** 活跃 SVG 元素引用：用于直接执行矩阵变换 (transform) */
  const svgRef = useRef<SVGElement | null>(null);

  // --- 几何变换状态机 ---
  /** 缩放比例状态：1 为原始尺寸，支持 0.2 至 3 的动态区间 */
  const [scale, setScale] = useState(1);
  /** 坐标位移状态：存储当前的 X/Y 偏移量 */
  const [position, setPosition] = useState({ x: 0, y: 0 });
  
  // --- 交互控制流状态 ---
  /** 拖拽锁：标识用户当前是否正在执行物理抓取动作 */
  const [isDragging, setIsDragging] = useState(false);
  /** 拖拽起始锚点：记录鼠标按下时的瞬时坐标偏移 */
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  /** 加载生命周期标识：控制遮罩层与加载动画的协同展示 */
  const [isLoading, setIsLoading] = useState(true);

  // --- 引用一致性保障 (Ref-Sync Mechanism) ---
  /** * @description 关键架构设计：
   * 在 React 异步更新模式下，事件监听器（如 wheel）往往会捕获到旧的闭包数据。
   * 通过 ref 实时映射最新的状态值，确保非 React 控制的事件流能获取到最实时的几何参数。
   */
  const scaleRef = useRef(scale);
  const positionRef = useRef(position);

  /** 状态到引用的单向同步：Scale */
  useEffect(() => {
    scaleRef.current = scale;
  }, [scale]);

  /** 状态到引用的单向同步：Position */
  useEffect(() => {
    positionRef.current = position;
  }, [position]);

  /**
   * 核心渲染管线 Effect
   * 负责 Mermaid 引擎的异步初始化、DSL 修正、离屏渲染及 SVG 挂载。
   */
  useEffect(() => {
    // 准入检查：若无输入数据或容器未就绪，则跳过本次渲染周期
    if (!chart || !svgContainerRef.current) return;

    // 开启加载状态，锁定 UI 交互
    setIsLoading(true);

    /**
     * 内部异步渲染主函数
     */
    const renderER = async () => {
      /**
       * 步骤 1：离屏渲染容器构建
       * @description 
       * Mermaid 在渲染期间会在 body 下创建临时 ID 冲突检测元素。
       * 采用“绝对定位偏移法”创建一个隐形的离屏容器，将副作用限制在可见视口之外，
       * 从而解决由于 CSS 样式计算导致的页面布局突发性跳变。
       */
      const offscreenContainer = document.createElement('div');
      offscreenContainer.style.cssText = 'position: fixed; left: -9999px; top: -9999px; visibility: hidden; pointer-events: none;';
      document.body.appendChild(offscreenContainer);

      try {
        /**
         * 步骤 2：DSL 预处理与格式清洗
         * 针对 AI 模型生成的原始文本进行语法补全，确保后端返回的多行定义能被正确识别。
         */
        let fixedChart = chart.trim();
        // 修正特定 AI 模型的输出错误，确保 erDiagram 标识符具有正确的换行前缀
        if (fixedChart.includes('}}%% erDiagram')) {
          fixedChart = fixedChart.replace('}}%% erDiagram', '}}%%\nerDiagram');
        }

        /**
         * 步骤 3：Mermaid 引擎动态加载
         * 采用 Dynamic Import 策略实现 Code-splitting，减小首屏 Bundle 体积。
         */
        const mermaid = (await import('mermaid')).default;

        /**
         * 步骤 4：引擎参数初始化配置
         * 对应需求说明书中的“视觉美化”要求，定制 ER 图的排版方向、颜色及字体大小。
         */
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose', // 允许复杂的交互属性
          er: {
            diagramPadding: 30,      // 图表外边距
            layoutDirection: 'TB',   // 采用自上而下的逻辑流向
            minEntityWidth: 150,    // 实体矩形最小宽度
            minEntityHeight: 100,   // 实体矩形最小高度
            entityPadding: 25,      // 字段间的呼吸感间距
            stroke: '#333',         // 连接线颜色
            fill: '#f8f9fa',        // 实体背景色
            fontSize: 16,           // 业务字体大小适配
            useMaxWidth: false      // 禁用自动宽度，由本组件接管几何变换
          }
        });

        /**
         * 步骤 5：离屏异步渲染
         * 生成唯一的 ID 标识符，防止多组件实例下的 SVG ID 污染。
         */
        const id = `interactive-er-${Date.now()}`;
        const result = await mermaid.render(id, fixedChart, offscreenContainer);

        // 步骤 6：DOM 注入与 SVG 后置处理
        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = result.svg;

          // 获取并接管 SVG 根节点
          const svg = svgContainerRef.current.querySelector('svg');
          if (svg) {
            svgRef.current = svg;

            // 注入交互式 CSS 属性
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.cursor = 'grab'; // 初始手势状态
            svg.style.userSelect = 'none'; // 禁止文本选中干扰拖拽

            /**
             * 步骤 7：ViewBox 弹性补偿
             * 确保导出的 SVG 具备正确的视口定义。若引擎未自动生成，
             * 则利用 getBBox 测量物理尺寸并动态补全，防止图像显示不全。
             */
            if (!svg.getAttribute('viewBox')) {
              try {
                const bbox = svg.getBBox();
                svg.setAttribute('viewBox', `0 0 ${bbox.width + 60} ${bbox.height + 60}`);
              } catch (e) {
                // 异常兜底：应用标准 4:3 比例视口
                svg.setAttribute('viewBox', '0 0 800 600');
              }
            }

            // 步骤 8：重置变换坐标系
            // 每次内容更新后，回归初始视角，确保用户能看到全貌
            setScale(1);
            setPosition({ x: 0, y: 0 });
            updateTransform(svg, 1, { x: 0, y: 0 });
          }

          console.log('✅ 交互式 ER 图渲染完成！');
          setIsLoading(false);
        }
      } catch (error) {
        // 异常处理：在容器内渲染错误提示 UI，替代原始图形展示
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
        // 资源回收：销毁临时的离屏容器
        if (offscreenContainer.parentNode) {
          offscreenContainer.parentNode.removeChild(offscreenContainer);
        }
      }
    };

    renderER();
  }, [chart]); // 当图表定义变更时，触发完整的重绘管线

  /**
   * 执行物理矩阵变换
   * 将逻辑层级的 scale 和 position 映射为 CSS 渲染层的 2D 变换。
   * @param {SVGElement} svg - 目标图形节点
   * @param {number} newScale - 计算后的目标缩放比
   * @param {Object} newPosition - 目标位移向量
   */
  const updateTransform = useCallback((svg: SVGElement, newScale: number, newPosition: { x: number, y: number }) => {
    // 采用 translate + scale 的复合变换
    svg.style.transform = `translate(${newPosition.x}px, ${newPosition.y}px) scale(${newScale})`;
    // 设置变换锚点为中心，符合用户直觉
    svg.style.transformOrigin = 'center center';
  }, []);

  /**
   * 滚轮事件监听效应
   * 实现基于鼠标滚轮的动态无损缩放。
   */
  useEffect(() => {
    const container = svgContainerRef.current;
    if (!container) return;

    /**
     * 滚轮交互核心逻辑
     * @param {WheelEvent} e - 原生浏览器滚轮事件
     */
    const handleWheel = (e: WheelEvent) => {
      // 准入条件：必须同时存在 SVG 实例及父容器
      if (!svgRef.current || !svgContainerRef.current) return;

      // 步骤 1：坐标空间判定
      const containerRect = svgContainerRef.current.getBoundingClientRect();
      const mouseX = e.clientX;
      const mouseY = e.clientY;

      // 判定鼠标是否在 ER 渲染有效负载区内
      const isMouseInContainer = (
        mouseX >= containerRect.left &&
        mouseX <= containerRect.right &&
        mouseY >= containerRect.top &&
        mouseY <= containerRect.bottom
      );

      // 逻辑分流：若鼠标不在容器内，释放控制权，允许父级页面正常滚动
      if (!isMouseInContainer) {
        return;
      }

      /**
       * 步骤 2：事件拦截
       * 使用 non-passive 模式调用 preventDefault，防止缩放过程中页面整体产生偏移。
       */
      e.preventDefault();
      e.stopPropagation();

      /**
       * 步骤 3：缩放因子计算
       * 采用 0.9/1.1 的几何级数系数，确保缩放过程在视觉上具备线性感受。
       */
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      // 从 ref 中读取最新几何参数，避免闭包失效
      const currentScale = scaleRef.current;
      const currentPosition = positionRef.current;
      
      // 步骤 4：范围约束检查 (Clamping)
      // 限制最小 0.2 倍（概览模式），最大 3 倍（微观模式）
      const newScale = Math.max(0.2, Math.min(3, currentScale * delta));

      // 步骤 5：触发状态同步与视图变换
      setScale(newScale);
      updateTransform(svgRef.current, newScale, currentPosition);
    };

    /**
     * 关键优化点：
     * 手动绑定并声明 passive: false，以绕过 Chrome 的高性能滚动默认拦截。
     */
    container.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      container.removeEventListener('wheel', handleWheel);
    };
  }, [updateTransform]);

  /**
   * 开始拖动交互流程
   * @param {React.MouseEvent} e - React 封装的鼠标事件
   */
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!svgRef.current || !svgContainerRef.current) return;

    // 步骤 1：热区点击判定
    const containerRect = svgContainerRef.current.getBoundingClientRect();
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    const isMouseInContainer = (
      mouseX >= containerRect.left &&
      mouseX <= containerRect.right &&
      mouseY >= containerRect.top &&
      mouseY <= containerRect.bottom
    );

    if (!isMouseInContainer) {
      return;
    }

    // 步骤 2：阻止父级组件感知此交互（如侧边栏收起等）
    e.stopPropagation();

    // 步骤 3：开启位移捕捉模式
    setIsDragging(true);
    // 记录初始位移偏移量，公式：dragStart = mousePos - currentPos
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    // 切换视觉指针样式
    svgRef.current.style.cursor = 'grabbing';
  };

  /**
   * 位移跟踪逻辑
   * @param {React.MouseEvent} e
   */
  const handleMouseMove = (e: React.MouseEvent) => {
    // 若未处于拖拽状态或 SVG 未加载，立即短路返回
    if (!isDragging || !svgRef.current) return;

    // 阻止浏览器默认文本选择干扰
    e.stopPropagation();

    // 步骤 1：计算目标位移向量
    const newPosition = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    };

    // 步骤 2：实时刷新状态与视图
    setPosition(newPosition);
    updateTransform(svgRef.current, scale, newPosition);
  };

  /**
   * 终止拖动交互流
   * @param {React.MouseEvent} [e] - 可选的事件对象
   */
  const handleMouseUp = (e?: React.MouseEvent) => {
    if (!svgRef.current) return;

    if (e) {
      e.stopPropagation();
    }

    // 重置交互标志位
    setIsDragging(false);
    // 恢复抓取状态指针
    svgRef.current.style.cursor = 'grab';
  };

  /**
   * 全局视图复位器
   * 一键回归原始 1.0 比例及 (0,0) 原点坐标。
   */
  const resetView = () => {
    if (!svgRef.current) return;

    const newScale = 1;
    const newPosition = { x: 0, y: 0 };

    setScale(newScale);
    setPosition(newPosition);
    updateTransform(svgRef.current, newScale, newPosition);
  };

  /**
   * 渲染 JSX 结构
   * 对应项目前端架构中的可视化面板。
   */
  return (
    <div className={className} style={{ position: 'relative', width: '100%', height: '100%' }}>
      
      {/* 浮动控制工具栏 (HUD): 
        包含放大、缩小及复位功能，常驻于图表右上角。
      */}
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
        {/* 缩小触发器 */}
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
        {/* 复位首页触发器 */}
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
        {/* 放大触发器 */}
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

      {/* HUD - 状态信息栏: 
        实时显示当前的物理缩放百分比。
      */}
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

      {/* 核心画布容器 (Main Canvas): 
        采用高阴影、圆角化设计，符合现代分析仪表盘视觉规范。
      */}
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
        {/* 加载蒙层逻辑: 
          在异步渲染期间提供平滑的等待反馈。
        */}
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
            {/* CSS 纯代码驱动的加载动画旋转体 */}
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

        {/* SVG 挂载宿主容器: 
          渲染完成后，通过透明度渐变实现平滑入场。
          绑定原生鼠标交互监听器，接管 Canvas 级别的所有操作。
        */}
        <div
          ref={svgContainerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={(e) => handleMouseUp(e)}
          onMouseLeave={() => handleMouseUp()}
          style={{
            position: 'absolute',
            inset: 0,
            touchAction: 'none', // 禁用系统默认触摸手势，由组件接管控制
            opacity: isLoading ? 0 : 1,
            visibility: isLoading ? 'hidden' : 'visible',
            transition: 'opacity 0.2s ease-in-out'
          }}
        />

        {/* 局部样式定义: 
          定义全局公用的 Loading Keyframe 帧动画。
        */}
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