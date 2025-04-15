using System;
using System.Collections.Generic;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.VisualBasic.FileIO;
using static System.Windows.Forms.VisualStyles.VisualStyleElement;
using ToolTip = System.Windows.Forms.ToolTip;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.TaskbarClock;
using System.ComponentModel.DataAnnotations;
using static System.Runtime.InteropServices.JavaScript.JSType;
using System.Numerics;
using System.Diagnostics;
using System.DirectoryServices.ActiveDirectory;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.ToolBar;
using System.Resources;
using System.Security.Policy;

namespace StepLogViewer
{
    public enum GanttType
    {
        bool_field, scalar_field
    }
    public class GanttData
    {
        public GanttData() { }
        public GanttType _type = GanttType.bool_field;
        public bool flag_grayBar = false;
        public double StartTime_sec = 0;
        public double Duration_sec = 0.001; //1ms
        public double EndTime_sec { get { return StartTime_sec + Duration_sec; } }
        public virtual string GetDescription()
        {
            return string.Format($"{Math.Round(Duration_sec, 3)} sec");
        }
    }

    public class ScalarData : GanttData
    {
        public ScalarData()
        {
            _type = GanttType.scalar_field;
        }
        public double Value = 0.0;
        public override string GetDescription()
        {
            return string.Format($"{Value}");
        }
    }

    public abstract class Field
    {
        public Field() { }
        public int index = 0;
        public int drawIndex = 0;
        public GanttType fieldType = GanttType.bool_field;
        public string Name = "";

        public List<GanttData> dataList = new List<GanttData>();
        public abstract int DrawData(Graphics gfx, int top);
        public abstract int DrawTitle(Graphics gfx, int top);
        public SolidBrush brush = null;
        public SolidBrush grayBrush = null;
    }

    public class BoolField : Field
    {
        public BoolField(string name)
        {
            this.Name = name;
            fieldType = GanttType.bool_field;

            grayBrush = new SolidBrush(Color.LightGray);
        }

        public override int DrawData(Graphics gfx, int top)
        {
            using (brush = new SolidBrush(DrawProperties.Inst.GetColor(drawIndex)))
            {
                top += DrawProperties.Inst.graphHeightMargin / 2 - DrawProperties.Inst.VScrollOffset_px;
                gfx.DrawString(Name, DrawProperties.Inst.FieldNameFont, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.fieldNameStartX, top);

                int left_base_px = DrawProperties.Inst.GraphStartLeftX_px - DrawProperties.Inst.SecToPixel(DrawProperties.Inst.HScrollOffset_sec);

                foreach (var data in dataList)
                {
                    int left_px = left_base_px + DrawProperties.Inst.SecToPixel(data.StartTime_sec);
                    Rectangle rect = new Rectangle(left_px, top, DrawProperties.Inst.SecToPixel(data.Duration_sec), DrawProperties.Inst.barHeight);

                    // DrawProperties.Inst.MousePos is in rect?
                    bool isSelected = rect.Contains(DrawProperties.Inst.CurrentMousePos_px);

                    if (isSelected)
                    {
                        DrawProperties.Inst.SelectedTime_sec[0] = data.StartTime_sec;
                        DrawProperties.Inst.SelectedTime_sec[1] = data.Duration_sec;

                        gfx.FillRectangle(DrawProperties.Inst.brushSelected, rect);
                        gfx.DrawRectangle(DrawProperties.Inst.selectedPen, rect); // Draw the border around the rectangle
                        gfx.DrawString(data.GetDescription(), DrawProperties.Inst.SelectedDataFont, DrawProperties.Inst.brushFontSelected, left_px, top);

                        // vertival grid line
                        //gfx.DrawLine(DrawProperties.Inst.selectedTimeLengthPen, rect.Left, DrawProperties.Inst.ClientRect.Top, rect.Left, DrawProperties.Inst.ClientRect.Bottom);
                        //gfx.DrawLine(DrawProperties.Inst.selectedTimeLengthPen, rect.Right, DrawProperties.Inst.ClientRect.Top, rect.Right, DrawProperties.Inst.ClientRect.Bottom);
                        //
                        //gfx.DrawString($"{Math.Round(data.StartTime_sec, 3)} sec", DrawProperties.Inst.Calibri10, DrawProperties.Inst.FieldNameBrush, new PointF(rect.Left, DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight));
                        //gfx.DrawString($"{Math.Round(data.StartTime_sec + data.Duration_sec, 3)} sec", DrawProperties.Inst.Calibri10, DrawProperties.Inst.FieldNameBrush, new PointF(rect.Right, DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight));
                    }
                    else
                    {
                        if (data.flag_grayBar)
                            gfx.FillRectangle(brush, rect);
                        else
                            gfx.FillRectangle(grayBrush, rect);
                    }
                }
            }
            return DrawProperties.Inst.barHeight;
        }
        public override int DrawTitle(Graphics gfx, int top)
        {
            top += DrawProperties.Inst.graphHeightMargin / 2 - DrawProperties.Inst.VScrollOffset_px; ;

            gfx.DrawString(Name, DrawProperties.Inst.FieldNameFont, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.fieldNameStartX, top);

            return DrawProperties.Inst.barHeight;
        }
    }

    public class ScalarField : Field
    {
        public double minVal = double.MaxValue;
        public double maxVal = double.MinValue;
        public SolidBrush brush = new SolidBrush(DrawProperties.Inst.ScalarBoxColor);

        public ScalarField(string name)
        {
            this.Name = name;
            fieldType = GanttType.scalar_field;
        }
        public void AddData(double time, double value)
        {
            this.dataList.Add(new ScalarData { StartTime_sec = time, Value = value });
            if (minVal > value) minVal = value;
            if (maxVal < value) maxVal = value;
        }

        //public int height_px { get; set; } = 100;

        public override int DrawData(Graphics gfx, int top)
        {
            top += DrawProperties.Inst.graphHeightMargin / 2 - +DrawProperties.Inst.VScrollOffset_px; ;
            int left_px = DrawProperties.Inst.GraphStartLeftX_px - DrawProperties.Inst.SecToPixel(DrawProperties.Inst.HScrollOffset_sec);
            foreach (ScalarData data in dataList)
            {
                int nLeft = left_px + DrawProperties.Inst.SecToPixel(data.StartTime_sec);
                double size = maxVal - minVal + 0.0001;
                double v = data.Value - minVal;
                double offset_per = v / size;
                int nSize = (int)(DrawProperties.Inst.scalarHeight * offset_per);
                int r_top = top + (DrawProperties.Inst.scalarHeight - nSize);
                //var rect = new Rectangle(nLeft, r_top, DrawProperties.Inst.ScalarBoxWidth, nSize);
                var rect = new Rectangle(nLeft, r_top, 6, 6);
                bool isSelected = rect.Contains(DrawProperties.Inst.CurrentMousePos_px);

                if (isSelected)
                {
                    //gfx.FillRectangle(DrawProperties.Inst.brushSelected, rect);
                    gfx.FillEllipse(DrawProperties.Inst.brushSelected, rect);
                    gfx.DrawRectangle(DrawProperties.Inst.selectedPen, rect); // Draw the border around the rectangle
                    gfx.DrawString(data.GetDescription(), DrawProperties.Inst.SelectedDataFont, brush, nLeft + DrawProperties.Inst.ScalarBoxWidth + 2, r_top);
                }
                else
                {
                    //gfx.FillRectangle(brush, rect);
                    gfx.FillEllipse(brush, rect);
                }

            }
            return DrawProperties.Inst.scalarHeight;
        }

        public override int DrawTitle(Graphics gfx, int top)
        {
            top += DrawProperties.Inst.graphHeightMargin / 2 - DrawProperties.Inst.VScrollOffset_px; ;
            gfx.DrawLine(DrawProperties.Inst.scalarGuideLinePen, DrawProperties.Inst.GraphStartLeftX_px, top, DrawProperties.Inst.ClientRect.Right, top);
            int bottom = top + DrawProperties.Inst.scalarHeight;
            gfx.DrawLine(DrawProperties.Inst.scalarGuideLinePen, DrawProperties.Inst.GraphStartLeftX_px, bottom, DrawProperties.Inst.ClientRect.Right, bottom);
            int mid = (top + bottom) / 2;
            gfx.DrawLine(DrawProperties.Inst.scalarGuideLinePen, DrawProperties.Inst.GraphStartLeftX_px, mid, DrawProperties.Inst.ClientRect.Right, mid);

            double midValue = Math.Round((minVal + maxVal) / 2, 1);
            int nameposY = top + DrawProperties.Inst.scalarHeight / 4;
            gfx.DrawString(Name, DrawProperties.Inst.FieldNameFont, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.fieldNameStartX, nameposY);
            gfx.DrawString(this.maxVal.ToString(), DrawProperties.Inst.FieldNameFontSmall, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.GraphStartLeftX_px, top);
            gfx.DrawString(midValue.ToString(), DrawProperties.Inst.FieldNameFontSmall, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.GraphStartLeftX_px, mid);
            gfx.DrawString(this.minVal.ToString(), DrawProperties.Inst.FieldNameFontSmall, DrawProperties.Inst.FieldNameBrush, DrawProperties.Inst.GraphStartLeftX_px, bottom);

            return DrawProperties.Inst.scalarHeight;
        }
    }
    public class HoverInfo
    {
        public double CurrentTime { get; set; }
        public int ActiveBarCount { get; set; }
    }


    ////////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////

    public sealed class DrawProperties
    {
        private static readonly Lazy<DrawProperties> _instance = new Lazy<DrawProperties>(() => new DrawProperties());

        // Private constructor to prevent instantiation
        private DrawProperties()
        {
            xAxisPenThin.DashStyle = DashStyle.Dash;
            scalarGuideLinePen.DashStyle = DashStyle.Dot;
        }

        public static DrawProperties Inst => _instance.Value;
        List<Color> ganttColors = new List<Color>
        {
            Color.FromArgb(155, 187, 89),
            Color.FromArgb(128, 100, 162),
            Color.FromArgb(31, 73, 125),
            Color.FromArgb(74, 172, 198),
            Color.FromArgb(247, 150, 70),
            Color.FromArgb(192, 79, 76)
        };
        public void Reset()
        {
            xAxisTimeGuidePos_sec = MouseCurrentTime_sec = -1;
            CurrentMousePos_px = new Point();
            SelectedTime_sec = new double[2];
            secToPixelScale = 50;
            HScrollOffset_sec = VScrollOffset_px = 0;
        }
        public Color GetColor(int index) => ganttColors[index % ganttColors.Count];
        public Color GraphBkgColor { get { return Color.FromArgb(239, 247, 254); } }
        public Color ScalarBoxColor { get { return Color.Purple; } }


        public Rectangle ClientRect { get; set; }
        //public Point xAxisTimeGuidePos_px = new Point();
        public double xAxisTimeGuidePos_sec = -1;
        public double MouseCurrentTime_sec = -1;
        public Point CurrentMousePos_px = new Point();

        public SolidBrush brushSelected = new SolidBrush(Color.LightGreen);
        public SolidBrush brushFontSelected = new SolidBrush(Color.DarkRed);
        public Pen selectedPen = new Pen(Color.DarkGreen, 2);
        public Pen selectedTimeLengthPen = new Pen(Color.Red, 1);

        public Pen xAxisPenThick = new Pen(Color.FromArgb(104, 146, 181), 3);
        public Pen xAxisPenThin = new Pen(Color.FromArgb(104, 146, 181), 1);
        public Pen xAxisCurrentTimePen = new Pen(Color.MediumPurple, 2);
        public Pen scalarGuideLinePen = new Pen(Color.FromArgb(65, 82, 170), 1);

        public SolidBrush FieldNameBrush = new SolidBrush(Color.FromArgb(52, 70, 112));
        public SolidBrush FieldBkgBrush = new SolidBrush(Color.FromArgb(219, 235, 250));
        public SolidBrush CurrentTimeBrush = new SolidBrush(Color.DarkRed);

        public Font SelectedDataFont = new Font("Calibri", 9, FontStyle.Bold);
        public Font FieldNameFont = new Font("Calibri", 11, FontStyle.Bold);
        public Font FieldNameFontSmall = new Font("Calibri", 9, FontStyle.Bold);
        public Font Calibri10Blod = new Font("Calibri", 10, FontStyle.Bold);
        public Font Calibri10 = new Font("Calibri", 10);

        public double[] SelectedTime_sec = new double[2]; // [start time, duration] sec

        public int barHeight { get; set; } = 20;
        public int scalarHeight { get; set; } = 100;
        public int ScalarBoxWidth { get; set; } = 5;
        public int graphHeightMargin { get; set; } = 20;

        public int fieldNameStartX { get; set; } = 20;
        public int TimeAxisHeight { get; set; } = 30;
        public double timeAxisGridInterval_sec { get; set; } = 10;
        public int GraphStartLeftX_px { get; set; } = 100;
        public double secToPixelScale { get; set; } = 50; // 50pixel per one second.
        public int HScrollOffset_sec { get; set; } = 0;
        public int VScrollOffset_px { get; set; } = 0;

        public double PixelToSec(int px) { return px / secToPixelScale; }
        public int SecToPixel(double sec) { return (int)((sec) * secToPixelScale); }
    }

    public class GanttChartControl : UserControl
    {
        private List<Field> fields = new List<Field>();
        public double totalEndTime_sec { get; private set; } = 0;
        private ToolTip toolTip = new ToolTip();
        private Panel chartPanel;
        private PictureBox pictureBox1;
        private ToolStrip toolStrip1;
        private VScrollBar vScrollBar1;
        private HScrollBar hScrollBar1;
        private ToolStripButton toolStripButton_ZoomIn;
        private ToolStripButton toolStripButton_ZoomOut;
        private ToolStripButton toolStripButton_ClearGuide;
        private bool isDragging = false;
        private Action<double> timeChangedEvent = null;
        public GanttChartControl()
        {
            chartPanel = new Panel { Location = new Point(10, 50), Size = new Size(760, 500), BorderStyle = BorderStyle.FixedSingle };
            chartPanel.Dock = DockStyle.Fill;
            
            pictureBox1 = new System.Windows.Forms.PictureBox();
            toolStrip1 = new ToolStrip();
            toolStripButton_ZoomIn = new ToolStripButton();
            toolStripButton_ZoomOut = new ToolStripButton();
            vScrollBar1 = new VScrollBar();
            hScrollBar1 = new HScrollBar();
            toolStripButton_ClearGuide = new ToolStripButton();
            // 
            // toolStrip1
            // 
            toolStrip1.ImageScalingSize = new Size(20, 20);
            toolStrip1.Items.AddRange(new ToolStripItem[] { toolStripButton_ZoomIn, toolStripButton_ZoomOut, toolStripButton_ClearGuide });
            toolStrip1.Location = new Point(0, 0);
            toolStrip1.Name = "toolStrip1";
            toolStrip1.Size = new Size(1012, 27);
            toolStrip1.TabIndex = 2;
            toolStrip1.Text = "toolStrip1";
            // 
            // toolStripButton_ZoomIn
            // 
            toolStripButton_ZoomIn.DisplayStyle = ToolStripItemDisplayStyle.Text;
            toolStripButton_ZoomIn.ImageTransparentColor = Color.Magenta;
            toolStripButton_ZoomIn.Name = "toolStripButton_ZoomIn";
            toolStripButton_ZoomIn.Size = new Size(29, 24);
            toolStripButton_ZoomIn.Text = "+";
            toolStripButton_ZoomIn.Click += toolStripButton_ZoomIn_Click;
            // 
            // toolStripButton_ZoomOut
            // 
            toolStripButton_ZoomOut.DisplayStyle = ToolStripItemDisplayStyle.Text;
            toolStripButton_ZoomOut.ImageTransparentColor = Color.Magenta;
            toolStripButton_ZoomOut.Name = "toolStripButton_ZoomOut";
            toolStripButton_ZoomOut.Size = new Size(29, 24);
            toolStripButton_ZoomOut.Text = "-";
            toolStripButton_ZoomOut.Click += toolStripButton_ZoomOut_Click;
            // 
            // toolStripButton_ClearGuide
            // 
            toolStripButton_ClearGuide.DisplayStyle = ToolStripItemDisplayStyle.Text;
            toolStripButton_ClearGuide.ImageTransparentColor = Color.Magenta;
            toolStripButton_ClearGuide.Name = "toolStripButton_ClearGuide";
            toolStripButton_ClearGuide.Size = new Size(29, 24);
            toolStripButton_ClearGuide.Text = "x";
            toolStripButton_ClearGuide.Click += toolStripButton_ClearGuide_Click;
            // 
            // vScrollBar1
            // 
            vScrollBar1.Dock = DockStyle.Right;
            vScrollBar1.Location = new Point(1012, 0);
            vScrollBar1.Name = "vScrollBar1";
            vScrollBar1.Size = new Size(17, 583);
            vScrollBar1.TabIndex = 1;
            vScrollBar1.Scroll += vScroll;
            // 
            // hScrollBar1
            // 
            hScrollBar1.Dock = DockStyle.Bottom;
            hScrollBar1.Location = new Point(0, 583);
            hScrollBar1.Name = "hScrollBar1";
            hScrollBar1.Size = new Size(1029, 17);
            hScrollBar1.TabIndex = 0;
            hScrollBar1.Scroll += hScroll;
            // 
            // pictureBox1
            // 
            this.pictureBox1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.pictureBox1.Cursor = System.Windows.Forms.Cursors.Cross;
            this.pictureBox1.Dock = System.Windows.Forms.DockStyle.Fill;
            this.pictureBox1.Location = new System.Drawing.Point(0, 0);
            this.pictureBox1.Name = "pictureBox1";
            this.pictureBox1.Size = new System.Drawing.Size(723, 339);
            this.pictureBox1.TabIndex = 2;
            this.pictureBox1.TabStop = false;
            //this.pictureBox1.KeyDown += new System.Windows.Forms.KeyEventHandler(this.Form1_KeyDown);
            //this.pictureBox1.Click += new System.EventHandler(this.pictureBox1_Click);
            this.pictureBox1.Paint += pictureBox_Paint;
            this.pictureBox1.MouseClick += pictureBox_MouseClick;
            this.pictureBox1.MouseDoubleClick += pictureBox_MouseDoubleClick;
            this.pictureBox1.MouseDown += pictureBox_MouseDown;
            this.pictureBox1.MouseMove += pictureBox_MouseMove;
            this.pictureBox1.MouseUp += pictureBox_MouseUp;
            this.pictureBox1.MouseWheel += pictureBox_MouseWheel;

            chartPanel.Controls.Add(pictureBox1);
            chartPanel.Controls.Add(toolStrip1);
            chartPanel.Controls.Add(vScrollBar1);
            chartPanel.Controls.Add(hScrollBar1);
            
            this.Controls.Add(chartPanel);

            //AddSampleData();
        }
        public void AddSampleData()
        {
            Random random = new Random();
            int i = 0;

            AddField(GanttType.bool_field, "Unit1_1");
            AddField(GanttType.bool_field, "Unit1_2");
            AddField(GanttType.bool_field, "Unit2_1");
            AddField(GanttType.bool_field, "Unit2_2");
            AddField(GanttType.bool_field, "Arm1");
            AddField(GanttType.bool_field, "Arm2");

            AddField(GanttType.scalar_field, "Reward");

            AddGanttData("Arm1", 0, 1, false);
            AddGanttData("Unit1_1", 3, 6, false);
            //timeLine.AddGanttData("Unit1_1", 3.5, 5, 4);
            AddGanttData("Arm1", 7, 10, false);
            //timeLine.AddGanttData("Unit2_1", 7, 27, 0);
            //timeLine.AddGanttData("Unit2_1", 27, 29.5, 4);
            //timeLine.AddGanttData("Arm2", 29.5, 30.5, 0);

            AddScalarData("Reward", 0, -1);
            AddScalarData("Reward", 1.5, -2);
            AddScalarData("Reward", 3.5, 0);
            AddScalarData("Reward", 5, 1);
            AddScalarData("Reward", 7, -1);
            AddScalarData("Reward", 27, -2);
            AddScalarData("Reward", 29.5, -1);
            AddScalarData("Reward", 30.6, 10);

            InvokeDraw();
        }
       
        public void AddField(GanttType fieldType, string name)
        {
            if (fields.Exists(f => f.Name == name))
                throw new ArgumentException("Field with the same name already exists.");

            Field field = null;
            if (fieldType == GanttType.bool_field)
                field = new BoolField(name);
            else if (fieldType == GanttType.scalar_field)
                field = new ScalarField(name);
            else
                throw (new ArgumentException());

            field.index = field.drawIndex = fields.Count;
            fields.Add(field);

            vScrollBar1.Maximum = (int)(fields.Count * 5);
            vScrollBar1.LargeChange = 10;
            vScrollBar1.SmallChange = 1;
        }

        public void AddGanttData(string fieldName, double start_sec, double duration_sec, bool flag_grayBar)
        {
            var field = fields.Find(f => f.Name == fieldName && f.fieldType == GanttType.bool_field);
            if (field == null)
                throw new ArgumentException("Field not found or not a boolean type.");

            field.dataList.Add(new GanttData { StartTime_sec = start_sec, Duration_sec = duration_sec, flag_grayBar = flag_grayBar });
            if (totalEndTime_sec < field.dataList.Last().EndTime_sec)
                totalEndTime_sec = field.dataList.Last().EndTime_sec;

            hScrollBar1.Maximum = (int)(totalEndTime_sec + 1);
            hScrollBar1.LargeChange = 10;
            hScrollBar1.SmallChange = 1;
        }

        public void AddScalarData(string fieldName, double time, double value)
        {
            var field = fields.Find(f => f.Name == fieldName && f.fieldType == GanttType.scalar_field);
            if (field == null)
                throw new ArgumentException("Field not found or not a scalar type.");

            ((ScalarField)field).AddData(time, value);
            if (totalEndTime_sec < field.dataList.Last().EndTime_sec)
                totalEndTime_sec = field.dataList.Last().EndTime_sec;
        }

        public void Redraw(Graphics gfx)
        {
            pictureBox1.SuspendLayout();
            gfx.Clear(DrawProperties.Inst.GraphBkgColor);
            DrawProperties.Inst.ClientRect = pictureBox1.ClientRectangle;
            DrawField(gfx);
            DrawTimeAxis(gfx);
            pictureBox1.ResumeLayout();
        }

        public void DrawField(Graphics gfx)
        {
            // draw each data
            int currTop_px = 0;// DrawProperties.Inst.graphHeightMargin;
            Pen pen2 = new Pen(Color.White, 5);

            foreach (var field in fields)
            {
                currTop_px += field.DrawData(gfx, currTop_px) + DrawProperties.Inst.graphHeightMargin;
                gfx.DrawLine(pen2, DrawProperties.Inst.GraphStartLeftX_px, currTop_px, DrawProperties.Inst.ClientRect.Right, currTop_px);
            }
            int height = DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight;

            // Fill the field name area
            Rectangle barRect = new Rectangle(0, 0, DrawProperties.Inst.GraphStartLeftX_px, height);
            gfx.FillRectangle(DrawProperties.Inst.FieldBkgBrush, barRect);

            currTop_px = 0;// DrawProperties.Inst.graphHeightMargin;
            foreach (var field in fields)
                currTop_px += field.DrawTitle(gfx, currTop_px) + DrawProperties.Inst.graphHeightMargin;
        }



        public void DrawTimeAxis(Graphics gfx)
        {
            int y = DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight;
            // horizontal time line
            gfx.DrawLine(DrawProperties.Inst.xAxisPenThick, DrawProperties.Inst.GraphStartLeftX_px, y, ClientRectangle.Width, y);

            for (double x_sec = 0; true; x_sec += DrawProperties.Inst.timeAxisGridInterval_sec)
            {
                if (x_sec == 0)
                    continue;
                int x_px = DrawProperties.Inst.GraphStartLeftX_px + DrawProperties.Inst.SecToPixel(x_sec) - DrawProperties.Inst.SecToPixel(DrawProperties.Inst.HScrollOffset_sec);

                if (x_px > DrawProperties.Inst.ClientRect.Width)
                    break;
                // vertival grid line
                gfx.DrawLine(DrawProperties.Inst.xAxisPenThin, x_px, DrawProperties.Inst.ClientRect.Top, x_px, DrawProperties.Inst.ClientRect.Bottom);
                gfx.DrawString($"{x_sec}s", DrawProperties.Inst.Calibri10Blod, DrawProperties.Inst.FieldNameBrush, new PointF(x_px, y));
            }

            // current time guide line
            if (DrawProperties.Inst.xAxisTimeGuidePos_sec > 0)
            {
                int left_px = DrawProperties.Inst.SecToPixel(DrawProperties.Inst.xAxisTimeGuidePos_sec) + DrawProperties.Inst.GraphStartLeftX_px - DrawProperties.Inst.SecToPixel(DrawProperties.Inst.HScrollOffset_sec);

                double curSec = Math.Round(DrawProperties.Inst.xAxisTimeGuidePos_sec, 2);
                gfx.DrawLine(DrawProperties.Inst.xAxisCurrentTimePen, left_px, DrawProperties.Inst.ClientRect.Top, left_px, DrawProperties.Inst.ClientRect.Bottom);
                gfx.DrawString($"{curSec}s", DrawProperties.Inst.Calibri10, DrawProperties.Inst.CurrentTimeBrush, new PointF(left_px, y));
            }

            // selected gantt time guide line
            if (DrawProperties.Inst.SelectedTime_sec[0] > 0)
            {
                int left_base_px = DrawProperties.Inst.GraphStartLeftX_px - DrawProperties.Inst.SecToPixel(DrawProperties.Inst.HScrollOffset_sec);
                int left_px = left_base_px + DrawProperties.Inst.SecToPixel(DrawProperties.Inst.SelectedTime_sec[0]);
                int right_px = left_px + DrawProperties.Inst.SecToPixel(DrawProperties.Inst.SelectedTime_sec[1]);


                gfx.DrawLine(DrawProperties.Inst.selectedTimeLengthPen, left_px, DrawProperties.Inst.ClientRect.Top, left_px, DrawProperties.Inst.ClientRect.Bottom);
                gfx.DrawLine(DrawProperties.Inst.selectedTimeLengthPen, right_px, DrawProperties.Inst.ClientRect.Top, right_px, DrawProperties.Inst.ClientRect.Bottom);

                gfx.DrawString($"{Math.Round(DrawProperties.Inst.SelectedTime_sec[0], 3)} sec", DrawProperties.Inst.Calibri10, DrawProperties.Inst.FieldNameBrush, new PointF(left_px, DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight));
                gfx.DrawString($"{Math.Round(DrawProperties.Inst.SelectedTime_sec[0] + DrawProperties.Inst.SelectedTime_sec[1], 3)} sec", DrawProperties.Inst.Calibri10, DrawProperties.Inst.FieldNameBrush, new PointF(right_px, DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight));
            }
        }
        public void InvokeDraw()
        {
            pictureBox1.Invalidate();
        }
        public void Clear()
        {
            DrawProperties.Inst.Reset();
            fields.Clear();
            isDragging = false;
            totalEndTime_sec = 0;
            InvokeDraw();
        }
        private void pictureBox_Paint(object sender, PaintEventArgs e)
        {
            Redraw(e.Graphics);
        }
        private void pictureBox_MouseMove(object sender, MouseEventArgs e)
        {

            var sec = DrawProperties.Inst.PixelToSec(e.X - DrawProperties.Inst.GraphStartLeftX_px) + DrawProperties.Inst.HScrollOffset_sec;
            DrawProperties.Inst.MouseCurrentTime_sec = sec;

            if (isDragging)
            {

            }
            else
            {
                DrawProperties.Inst.CurrentMousePos_px.X = e.X;
                DrawProperties.Inst.CurrentMousePos_px.Y = e.Y;
            }


        }
        public void SetTimeChangeEvent(Action<double> timeChangedEvent)
        {
            this.timeChangedEvent = timeChangedEvent;
        }
        private void pictureBox_MouseDown(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left/* && ModifierKeys.HasFlag(Keys.Control)*/)
            {
                int y = DrawProperties.Inst.ClientRect.Bottom - DrawProperties.Inst.TimeAxisHeight;
                if (e.Y > y)
                {
                    isDragging = true;
                }
            }
        }

        private void pictureBox_MouseUp(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left && isDragging)
            {
                isDragging = false;
            }
        }

        private void pictureBox_MouseDoubleClick(object sender, MouseEventArgs e)
        {
            if(timeChangedEvent != null) 
                this.timeChangedEvent(DrawProperties.Inst.SelectedTime_sec[0]);
        }
        private void pictureBox_MouseWheel(object sender, MouseEventArgs e)
        {
            if ((Control.ModifierKeys & Keys.Control) == Keys.Control)
            {
                var curSec = DrawProperties.Inst.PixelToSec(e.X - DrawProperties.Inst.GraphStartLeftX_px) + DrawProperties.Inst.HScrollOffset_sec;
                if (e.Delta > 0)
                {
                    DrawProperties.Inst.secToPixelScale *= 1.1f;
                }
                else if (e.Delta < 0)
                {
                    DrawProperties.Inst.secToPixelScale /= 1.1f;
                }
                DrawProperties.Inst.secToPixelScale = Math.Clamp(DrawProperties.Inst.secToPixelScale, 5f, 100f);

                hScrollBar1.Value = (int)curSec;
                InvokeDraw();
            }
        }

        private void pictureBox_MouseClick(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                InvokeDraw();
            }
            else if (e.Button == MouseButtons.Right)
            {
            }
            else if (e.Button == MouseButtons.Middle)
            {
            }
        }


        public void hScroll(object sender, ScrollEventArgs e)
        {
            DrawProperties.Inst.HScrollOffset_sec = e.NewValue;
            InvokeDraw();
        }

        public void vScroll(object sender, ScrollEventArgs e)
        {
            DrawProperties.Inst.VScrollOffset_px = e.NewValue * (DrawProperties.Inst.barHeight / 2);
            InvokeDraw();
        }
        private void toolStripButton_ZoomIn_Click(object sender, EventArgs e)
        {
            DrawProperties.Inst.secToPixelScale *= 1.1f;
            DrawProperties.Inst.secToPixelScale = Math.Clamp(DrawProperties.Inst.secToPixelScale, 5f, 100f);
            InvokeDraw();
        }

        private void toolStripButton_ZoomOut_Click(object sender, EventArgs e)
        {
            DrawProperties.Inst.secToPixelScale /= 1.1f;
            DrawProperties.Inst.secToPixelScale = Math.Clamp(DrawProperties.Inst.secToPixelScale, 5f, 100f);
            InvokeDraw();
        }

        private void toolStripButton_ClearGuide_Click(object sender, EventArgs e)
        {
            DrawProperties.Inst.SelectedTime_sec[0] = DrawProperties.Inst.SelectedTime_sec[1] = -1;
            DrawProperties.Inst.xAxisTimeGuidePos_sec = -1;
            InvokeDraw();
        }
    }

}
