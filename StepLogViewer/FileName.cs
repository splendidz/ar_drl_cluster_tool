using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

public class GanttField
{
    public string Name { get; set; }
    public bool IsBoolType { get; set; }
    public Color Color { get; set; }
    public double ScalarTypeMin { get; set; }
    public double ScalarTypeMax { get; set; }
    public int ScalarTypeHeightPixel { get; set; }
    public List<GanttBar> Bars { get; set; } = new List<GanttBar>();
    public List<GanttScalar> Scalars { get; set; } = new List<GanttScalar>();
}

public class GanttBar
{
    public TimeSpan Start { get; set; }
    public TimeSpan Duration { get; set; }
    public Rectangle Rect { get; set; }
}

public class GanttScalar
{
    public TimeSpan Time { get; set; }
    public double Value { get; set; }
    public Rectangle Rect { get; set; }
}

public class HoverInfo
{
    public double CurrentTime { get; set; }
    public int ActiveBarCount { get; set; }
}

public class GanttChartData
{
    private List<GanttField> fields = new List<GanttField>();
    private double endTimeSec;
    private ToolTip toolTip = new ToolTip();

    private int barHeight = 20;
    private int barSpacing = 30;
    private int headerYOffset = 10;
    private int scalarHeight = 20;

    public int ZoomLevel { get; private set; } = 1;

    public void AddField(string name, bool isBoolType, Color color, double scalarTypeMin = 0, double scalarTypeMax = 0, int scalarTypeHeightPixel = 20)
    {
        if (fields.Exists(f => f.Name == name))
            throw new ArgumentException("Field with the same name already exists.");

        fields.Add(new GanttField
        {
            Name = name,
            IsBoolType = isBoolType,
            Color = color,
            ScalarTypeMin = scalarTypeMin,
            ScalarTypeMax = scalarTypeMax,
            ScalarTypeHeightPixel = scalarTypeHeightPixel
        });
    }

    public void Initialize(double endTimeSec)
    {
        this.endTimeSec = endTimeSec;
    }

    public void AddBarData(string fieldName, TimeSpan start, TimeSpan duration)
    {
        var field = fields.Find(f => f.Name == fieldName && f.IsBoolType);
        if (field == null)
            throw new ArgumentException("Field not found or not a boolean type.");

        field.Bars.Add(new GanttBar { Start = start, Duration = duration });
    }

    public void AddScalarData(string fieldName, TimeSpan time, double value)
    {
        var field = fields.Find(f => f.Name == fieldName && !f.IsBoolType);
        if (field == null)
            throw new ArgumentException("Field not found or not a scalar type.");

        field.Scalars.Add(new GanttScalar { Time = time, Value = value });
    }

    public void PrecomputeBarRects(int barStartLeftX, int barStartTopY, int availableWidth)
    {
        int widthPerItem = availableWidth / (int)endTimeSec;
        int fieldIndex = 0;

        foreach (var field in fields)
        {
            if (field.IsBoolType)
            {
                foreach (var bar in field.Bars)
                {
                    bar.Rect = GetBarRect(fieldIndex, (int)bar.Start.TotalSeconds, (int)(bar.Start.TotalSeconds + bar.Duration.TotalSeconds), barStartLeftX, barStartTopY, widthPerItem, barHeight);
                }
            }
            else
            {
                foreach (var scalar in field.Scalars)
                {
                    scalar.Rect = GetScalarRect(fieldIndex, scalar.Time, scalar.Value, barStartLeftX, barStartTopY, widthPerItem, scalarHeight, field.ScalarTypeMin, field.ScalarTypeMax);
                }
            }
            fieldIndex++;
        }
    }

    private Rectangle GetBarRect(int fieldIndex, int startSeconds, int endSeconds, int barStartLeftX, int barStartTopY, int widthPerItem, int barHeight)
    {
        int nLeft = barStartLeftX + (startSeconds * widthPerItem);
        int nTop = barStartTopY + (fieldIndex * (barHeight + 10)); // Adjust spacing
        int nWidth = (endSeconds - startSeconds) * widthPerItem;
        return new Rectangle(nLeft, nTop, nWidth, barHeight);
    }

    private Rectangle GetScalarRect(int fieldIndex, TimeSpan time, double value, int barStartLeftX, int barStartTopY, int widthPerItem, int scalarHeight, double scalarMin, double scalarMax)
    {
        int nLeft = barStartLeftX + (int)(time.TotalSeconds * widthPerItem);
        int nTop = barStartTopY + (fieldIndex * (barHeight + 10));
        int adjustedHeight = (int)((value - scalarMin) / (scalarMax - scalarMin) * scalarHeight);
        return new Rectangle(nLeft, nTop - adjustedHeight, 4, 4); // 4x4 dot for scalar values
    }

    public void DrawBars(Graphics gfx)
    {
        foreach (var field in fields)
        {
            if (field.IsBoolType)
            {
                foreach (var bar in field.Bars)
                {
                    using (var brush = new LinearGradientBrush(bar.Rect, field.Color, Color.White, LinearGradientMode.Vertical))
                    {
                        gfx.FillRectangle(brush, bar.Rect);
                    }
                    gfx.DrawRectangle(Pens.Black, bar.Rect);
                }
            }
        }
    }

    public void DrawScalars(Graphics gfx)
    {
        foreach (var field in fields)
        {
            if (!field.IsBoolType)
            {
                foreach (var scalar in field.Scalars)
                {
                    using (var brush = new SolidBrush(field.Color))
                    {
                        gfx.FillEllipse(brush, scalar.Rect);
                    }
                }
            }
        }
    }
}
