# app/services/overmind/art/generators.py
"""
🎨 CS73: Generative Art from Code
==================================

توليد فن إبداعي من البيانات البرمجية باستخدام الخوارزميات.

CS73 Principles:
- Algorithmic Art: الفن الخوارزمي
- Computational Creativity: الإبداع الحاسوبي
- Procedural Generation: التوليد الإجرائي
- Emergence: الظهور من البساطة
"""

import math
import random
from typing import Any

from app.services.overmind.art.styles import ArtStyle, VisualTheme


class CodePatternArtist:
    """
    فنان أنماط الكود التوليدية.
    
    CS73: كل مشروع برمجي له بصمته الفنية الفريدة.
    """
    
    def __init__(self, style: ArtStyle = ArtStyle.CYBERPUNK):
        """تهيئة الفنان"""
        self.style = style
        self.palette = VisualTheme.get_palette(style)
    
    def generate_fractal_tree(
        self,
        complexity: int = 5,
        seed: int | None = None
    ) -> str:
        """
        توليد شجرة فركتالية تمثل بنية الكود.
        
        CS73: الفركتالات تمثل التكرار والتشابه الذاتي في البرمجة.
        
        Args:
            complexity: مستوى العمق (عدد الفروع)
            seed: بذرة عشوائية للتكرار
            
        Returns:
            str: SVG fractal tree
            
        Complexity: O(2^n) where n is complexity level
        """
        if seed is not None:
            random.seed(seed)
        
        width, height = 600, 600
        start_x, start_y = width // 2, height - 50
        
        svg = f'''<svg width="{width}" height="{height}" 
                       xmlns="http://www.w3.org/2000/svg"
                       style="background: {self.palette.background};">
        '''
        
        # رسم الشجرة الفركتالية
        branches = self._draw_branch(
            start_x, start_y,
            -90,  # angle (up)
            100,  # length
            complexity,
            self.palette.primary
        )
        svg += branches
        
        svg += '''
            <text x="10" y="30" 
                  fill="%s"
                  font-size="16"
                  font-weight="bold">Fractal Code Tree</text>
        </svg>
        ''' % self.palette.text
        
        return svg
    
    def _draw_branch(
        self,
        x: float,
        y: float,
        angle: float,
        length: float,
        depth: int,
        color: str
    ) -> str:
        """
        رسم فرع بشكل تكراري (Recursive Fractal).
        
        CS73: التكرار يخلق جمالاً من البساطة.
        """
        if depth <= 0 or length < 2:
            return ""
        
        # حساب نقطة النهاية
        angle_rad = math.radians(angle)
        end_x = x + length * math.cos(angle_rad)
        end_y = y + length * math.sin(angle_rad)
        
        # تدرج اللون حسب العمق
        gradient = VisualTheme.create_gradient(
            self.palette.primary,
            self.palette.accent,
            steps=10
        )
        color_index = min(10 - depth, len(gradient) - 1)
        branch_color = gradient[color_index]
        
        # رسم الفرع
        svg = f'''
        <line x1="{x}" y1="{y}" 
              x2="{end_x}" y2="{end_y}"
              stroke="{branch_color}"
              stroke-width="{depth}"
              opacity="0.8"/>
        '''
        
        # فروع فرعية (recursive branches)
        new_length = length * 0.7
        angle_variation = 25 + random.uniform(-10, 10)
        
        # فرع أيسر
        svg += self._draw_branch(
            end_x, end_y,
            angle - angle_variation,
            new_length,
            depth - 1,
            color
        )
        
        # فرع أيمن
        svg += self._draw_branch(
            end_x, end_y,
            angle + angle_variation,
            new_length,
            depth - 1,
            color
        )
        
        return svg
    
    def generate_spiral_code(
        self,
        iterations: int = 100,
        data_seed: int = 42
    ) -> str:
        """
        توليد حلزون يمثل تطور الكود.
        
        CS73: الحلزون يرمز للنمو والتطور المستمر.
        
        Args:
            iterations: عدد التكرارات
            data_seed: بذرة البيانات
            
        Returns:
            str: SVG spiral art
            
        Complexity: O(n)
        """
        width, height = 600, 600
        center_x, center_y = width // 2, height // 2
        
        svg = f'''<svg width="{width}" height="{height}" 
                       xmlns="http://www.w3.org/2000/svg"
                       style="background: {self.palette.background};">
        '''
        
        # حساب نقاط الحلزون
        points = []
        for i in range(iterations):
            angle = i * (360 / 16) * math.pi / 180
            radius = 2 + i * 2
            
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))
        
        # رسم خطوط متصلة
        gradient = VisualTheme.create_gradient(
            self.palette.primary,
            self.palette.secondary,
            steps=iterations
        )
        
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            color = gradient[i]
            
            svg += f'''
            <line x1="{x1}" y1="{y1}" 
                  x2="{x2}" y2="{y2}"
                  stroke="{color}"
                  stroke-width="2"
                  opacity="0.8"/>
            '''
        
        svg += '''
            <text x="10" y="30" 
                  fill="%s"
                  font-size="16"
                  font-weight="bold">Code Evolution Spiral</text>
        </svg>
        ''' % self.palette.text
        
        return svg


class MetricsArtist:
    """
    فنان تصور المقاييس البرمجية.
    
    CS73: الأرقام يمكن أن تكون جميلة.
    """
    
    def __init__(self, style: ArtStyle = ArtStyle.NATURE):
        """تهيئة الفنان"""
        self.style = style
        self.palette = VisualTheme.get_palette(style)
    
    def create_radial_chart(
        self,
        metrics: dict[str, float],
        title: str = "Code Metrics"
    ) -> str:
        """
        إنشاء رسم بياني دائري فني.
        
        CS73: الدوائر أكثر جاذبية من الأعمدة التقليدية.
        
        Args:
            metrics: المقاييس المراد تصورها
            title: عنوان الرسم
            
        Returns:
            str: SVG radial chart
            
        Complexity: O(n) where n is number of metrics
        Note: تم تقسيم الدالة إلى helper methods لتطبيق KISS و SRP
        """
        width, height = 500, 500
        center_x, center_y = width // 2, height // 2
        max_radius = 180
        
        # بناء الـ SVG من المكونات
        svg = self._create_svg_header(width, height, title)
        svg += self._create_circular_grid(center_x, center_y, max_radius)
        
        if not metrics:
            return svg + '</svg>'
        
        points, metrics_svg = self._create_metric_points(
            metrics, center_x, center_y, max_radius
        )
        svg += metrics_svg
        svg += self._create_connecting_polygon(points)
        svg += '</svg>'
        
        return svg
    
    def _create_svg_header(self, width: int, height: int, title: str) -> str:
        """إنشاء رأس SVG مع العنوان."""
        return f'''<svg width="{width}" height="{height}" 
                       xmlns="http://www.w3.org/2000/svg"
                       style="background: {self.palette.background};">
            
            <text x="{width//2}" y="30" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="20"
                  font-weight="bold">{title}</text>
        '''
    
    def _create_circular_grid(
        self, center_x: int, center_y: int, max_radius: int
    ) -> str:
        """إنشاء الشبكة الدائرية للخلفية."""
        grid_svg = ""
        for i in range(1, 5):
            radius = (max_radius / 4) * i
            grid_svg += f'''
            <circle cx="{center_x}" cy="{center_y}" 
                    r="{radius}" 
                    fill="none"
                    stroke="{self.palette.secondary}"
                    stroke-width="1"
                    opacity="0.2"/>
            '''
        return grid_svg
    
    def _create_metric_points(
        self,
        metrics: dict[str, float],
        center_x: int,
        center_y: int,
        max_radius: int
    ) -> tuple[list[tuple[float, float]], str]:
        """إنشاء نقاط المقاييس وعناصر SVG الخاصة بها."""
        num_metrics = len(metrics)
        angle_step = 360 / num_metrics
        max_value = max(metrics.values()) if metrics else 1
        
        gradient = VisualTheme.create_gradient(
            self.palette.primary,
            self.palette.accent,
            steps=num_metrics
        )
        
        points = []
        svg = ""
        
        for i, (key, value) in enumerate(metrics.items()):
            point, point_svg = self._create_single_metric_point(
                i, key, value, angle_step, max_value, max_radius,
                center_x, center_y, gradient[i]
            )
            points.append(point)
            svg += point_svg
        
        return points, svg
    
    def _create_single_metric_point(
        self,
        index: int,
        key: str,
        value: float,
        angle_step: float,
        max_value: float,
        max_radius: int,
        center_x: int,
        center_y: int,
        color: str
    ) -> tuple[tuple[float, float], str]:
        """إنشاء نقطة مقياس واحدة مع عناصر SVG."""
        angle = index * angle_step - 90  # البداية من الأعلى
        angle_rad = math.radians(angle)
        
        normalized = value / max_value if max_value > 0 else 0
        radius = normalized * max_radius
        
        x = center_x + radius * math.cos(angle_rad)
        y = center_y + radius * math.sin(angle_rad)
        
        svg = f'''
            <line x1="{center_x}" y1="{center_y}" 
                  x2="{x}" y2="{y}"
                  stroke="{color}"
                  stroke-width="2"
                  opacity="0.6"/>
            
            <circle cx="{x}" cy="{y}" 
                    r="6" 
                    fill="{color}"/>
            
            <!-- Label -->
            <text x="{x + 15}" y="{y}" 
                  fill="{self.palette.text}"
                  font-size="12">{key}: {value:.1f}</text>
        '''
        
        return (x, y), svg
    
    def _create_connecting_polygon(self, points: list[tuple[float, float]]) -> str:
        """إنشاء المضلع الذي يربط النقاط."""
        if len(points) <= 2:
            return ""
        
        polygon_points = " ".join([f"{x},{y}" for x, y in points])
        return f'''
            <polygon points="{polygon_points}"
                     fill="{self.palette.primary}"
                     opacity="0.2"
                     stroke="{self.palette.primary}"
                     stroke-width="2"/>
        '''
    
    def create_bar_art(
        self,
        data: dict[str, float],
        title: str = "Artistic Bar Chart"
    ) -> str:
        """
        رسم بياني عمودي فني.
        
        CS73: حتى الرسوم البيانية التقليدية يمكن أن تكون فنية.
        
        Args:
            data: البيانات المراد عرضها
            title: العنوان
            
        Returns:
            str: SVG bar chart with artistic styling
            
        Note: تم تقسيم الدالة إلى helper methods لتطبيق KISS
        """
        width, height = 600, 400
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        svg = self._create_bar_chart_header(width, height, title)
        
        if not data:
            return svg + '</svg>'
        
        bar_config = self._calculate_bar_dimensions(data, chart_width, chart_height)
        bars_svg = self._draw_bars(data, bar_config, margin, height, chart_height)
        
        return svg + bars_svg + '</svg>'
    
    def _create_bar_chart_header(self, width: int, height: int, title: str) -> str:
        """إنشاء رأس الرسم البياني العمودي."""
        return f'''<svg width="{width}" height="{height}" 
                       xmlns="http://www.w3.org/2000/svg"
                       style="background: {self.palette.background};">
            
            <text x="{width//2}" y="30" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="20"
                  font-weight="bold">{title}</text>
        '''
    
    def _calculate_bar_dimensions(
        self,
        data: dict[str, float],
        chart_width: int,
        chart_height: int
    ) -> dict[str, Any]:
        """حساب أبعاد الأعمدة والتباعد."""
        num_bars = len(data)
        bar_width = chart_width / (num_bars * 2)
        spacing = bar_width
        max_value = max(data.values()) if data else 1
        
        gradient = VisualTheme.create_gradient(
            self.palette.primary,
            self.palette.secondary,
            steps=num_bars
        )
        
        return {
            "num_bars": num_bars,
            "bar_width": bar_width,
            "spacing": spacing,
            "max_value": max_value,
            "gradient": gradient,
        }
    
    def _draw_bars(
        self,
        data: dict[str, float],
        config: dict[str, Any],
        margin: int,
        height: int,
        chart_height: int
    ) -> str:
        """رسم جميع الأعمدة مع التسميات."""
        svg = ""
        bar_width = config["bar_width"]
        spacing = config["spacing"]
        max_value = config["max_value"]
        gradient = config["gradient"]
        
        for i, (key, value) in enumerate(data.items()):
            x = margin + i * (bar_width + spacing)
            normalized = value / max_value if max_value > 0 else 0
            bar_height = normalized * chart_height
            y = height - margin - bar_height
            color = gradient[i]
            
            svg += self._draw_single_bar(
                i, x, y, bar_width, bar_height, color, value, key, height, margin
            )
        
        return svg
    
    def _draw_single_bar(
        self,
        index: int,
        x: float,
        y: float,
        bar_width: float,
        bar_height: float,
        color: str,
        value: float,
        key: str,
        height: int,
        margin: int
    ) -> str:
        """رسم عمود واحد مع التدرج والتسميات."""
        return f'''
            <rect x="{x}" y="{y}" 
                  width="{bar_width}" 
                  height="{bar_height}"
                  fill="url(#grad{index})"
                  rx="5"/>
            
            <defs>
                <linearGradient id="grad{index}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:{color};stop-opacity:0.5" />
                </linearGradient>
            </defs>
            
            <!-- Value Label -->
            <text x="{x + bar_width/2}" y="{y - 5}" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="12"
                  font-weight="bold">{value:.1f}</text>
            
            <!-- Key Label -->
            <text x="{x + bar_width/2}" y="{height - margin + 20}" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="10"
                  transform="rotate(-45 {x + bar_width/2} {height - margin + 20})">
                {key}
            </text>
        '''


class NetworkArtist:
    """
    فنان تصور الشبكات والعلاقات.
    
    CS73: العلاقات البرمجية كشبكة عنكبوتية جميلة.
    """
    
    def __init__(self, style: ArtStyle = ArtStyle.DARK):
        """تهيئة الفنان"""
        self.style = style
        self.palette = VisualTheme.get_palette(style)
    
    def create_dependency_web(
        self,
        nodes: list[dict[str, Any]],
        edges: list[tuple[str, str]],
        title: str = "Code Dependencies"
    ) -> str:
        """
        إنشاء شبكة فنية للتبعيات.
        
        CS73: التبعيات كشبكة حياة متصلة.
        
        Args:
            nodes: قائمة العقد (modules, classes, etc.)
            edges: قائمة الاتصالات (من, إلى)
            title: العنوان
            
        Returns:
            str: SVG network visualization
            
        Complexity: O(n + e) where n is nodes, e is edges
        Note: تم تقسيم الدالة إلى helper methods لتطبيق KISS
        """
        width, height = 700, 700
        center_x, center_y = width // 2, height // 2
        radius = 250
        
        svg = self._create_network_header(width, height, title)
        
        if not nodes:
            return svg + '</svg>'
        
        node_positions = self._calculate_node_positions(
            nodes, center_x, center_y, radius
        )
        svg += self._draw_edges(edges, node_positions)
        svg += self._draw_nodes(nodes, node_positions)
        svg += '</svg>'
        
        return svg
    
    def _create_network_header(self, width: int, height: int, title: str) -> str:
        """إنشاء رأس الشبكة."""
        return f'''<svg width="{width}" height="{height}" 
                       xmlns="http://www.w3.org/2000/svg"
                       style="background: {self.palette.background};">
            
            <text x="{width//2}" y="30" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="20"
                  font-weight="bold">{title}</text>
        '''
    
    def _calculate_node_positions(
        self,
        nodes: list[dict[str, Any]],
        center_x: int,
        center_y: int,
        radius: int
    ) -> dict[str, tuple[float, float]]:
        """حساب مواقع العقد في دائرة."""
        num_nodes = len(nodes)
        angle_step = 360 / num_nodes
        node_positions: dict[str, tuple[float, float]] = {}
        
        for i, node in enumerate(nodes):
            angle = i * angle_step - 90
            angle_rad = math.radians(angle)
            
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            
            node_id = node.get("id", f"node_{i}")
            node_positions[node_id] = (x, y)
        
        return node_positions
    
    def _draw_edges(
        self,
        edges: list[tuple[str, str]],
        node_positions: dict[str, tuple[float, float]]
    ) -> str:
        """رسم الاتصالات بين العقد."""
        svg = ""
        for source, target in edges:
            if source in node_positions and target in node_positions:
                x1, y1 = node_positions[source]
                x2, y2 = node_positions[target]
                
                svg += f'''
                <line x1="{x1}" y1="{y1}" 
                      x2="{x2}" y2="{y2}"
                      stroke="{self.palette.secondary}"
                      stroke-width="1"
                      opacity="0.3"/>
                '''
        return svg
    
    def _draw_nodes(
        self,
        nodes: list[dict[str, Any]],
        node_positions: dict[str, tuple[float, float]]
    ) -> str:
        """رسم العقد مع التسميات."""
        num_nodes = len(nodes)
        gradient = VisualTheme.create_gradient(
            self.palette.primary,
            self.palette.accent,
            steps=num_nodes
        )
        
        svg = ""
        for i, node in enumerate(nodes):
            node_id = node.get("id", f"node_{i}")
            if node_id not in node_positions:
                continue
            
            x, y = node_positions[node_id]
            color = gradient[i]
            label = node.get("label", node_id)
            
            svg += f'''
            <circle cx="{x}" cy="{y}" 
                    r="20" 
                    fill="{color}"
                    stroke="{self.palette.background}"
                    stroke-width="3"/>
            
            <text x="{x}" y="{y + 35}" 
                  text-anchor="middle"
                  fill="{self.palette.text}"
                  font-size="11">{label}</text>
            '''
        
        return svg
