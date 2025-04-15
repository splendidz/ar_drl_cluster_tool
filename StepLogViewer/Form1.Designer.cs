namespace StepLogViewer
{
    partial class Form1
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            components = new System.ComponentModel.Container();
            panel1 = new Panel();
            splitContainer_big = new SplitContainer();
            splitContainer1 = new SplitContainer();
            listView_fileList = new ListView();
            splitContainer2 = new SplitContainer();
            listView_stepList = new ListView();
            splitContainer3 = new SplitContainer();
            dataGridView_Action = new DataGridView();
            toolStrip1 = new ToolStrip();
            toolStripLabel1 = new ToolStripLabel();
            splitContainer4 = new SplitContainer();
            dataGridView_Transport = new DataGridView();
            toolStrip2 = new ToolStrip();
            toolStripLabel2 = new ToolStripLabel();
            dataGridView_Unit = new DataGridView();
            toolStrip3 = new ToolStrip();
            toolStripLabel3 = new ToolStripLabel();
            statusStrip1 = new StatusStrip();
            toolStripStatusLabel_reward = new ToolStripStatusLabel();
            toolStripStatusLabel_totalStep = new ToolStripStatusLabel();
            toolStripStatusLabel_curr_time = new ToolStripStatusLabel();
            menuStrip1 = new MenuStrip();
            fileToolStripMenuItem = new ToolStripMenuItem();
            menu_selectDirecotry = new ToolStripMenuItem();
            menu_clear = new ToolStripMenuItem();
            menu_exit = new ToolStripMenuItem();
            infoToolStripMenuItem = new ToolStripMenuItem();
            menu_logInfo = new ToolStripMenuItem();
            timer1 = new System.Windows.Forms.Timer(components);
            panel1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer_big).BeginInit();
            splitContainer_big.Panel1.SuspendLayout();
            splitContainer_big.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer1).BeginInit();
            splitContainer1.Panel1.SuspendLayout();
            splitContainer1.Panel2.SuspendLayout();
            splitContainer1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer2).BeginInit();
            splitContainer2.Panel1.SuspendLayout();
            splitContainer2.Panel2.SuspendLayout();
            splitContainer2.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer3).BeginInit();
            splitContainer3.Panel1.SuspendLayout();
            splitContainer3.Panel2.SuspendLayout();
            splitContainer3.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)dataGridView_Action).BeginInit();
            toolStrip1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer4).BeginInit();
            splitContainer4.Panel1.SuspendLayout();
            splitContainer4.Panel2.SuspendLayout();
            splitContainer4.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)dataGridView_Transport).BeginInit();
            toolStrip2.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)dataGridView_Unit).BeginInit();
            toolStrip3.SuspendLayout();
            statusStrip1.SuspendLayout();
            menuStrip1.SuspendLayout();
            SuspendLayout();
            // 
            // panel1
            // 
            panel1.Controls.Add(splitContainer_big);
            panel1.Controls.Add(statusStrip1);
            panel1.Controls.Add(menuStrip1);
            panel1.Dock = DockStyle.Fill;
            panel1.Location = new Point(0, 0);
            panel1.Name = "panel1";
            panel1.Size = new Size(1930, 897);
            panel1.TabIndex = 0;
            // 
            // splitContainer_big
            // 
            splitContainer_big.BackColor = Color.White;
            splitContainer_big.Dock = DockStyle.Fill;
            splitContainer_big.Location = new Point(0, 28);
            splitContainer_big.Name = "splitContainer_big";
            splitContainer_big.Orientation = Orientation.Horizontal;
            // 
            // splitContainer_big.Panel1
            // 
            splitContainer_big.Panel1.Controls.Add(splitContainer1);
            splitContainer_big.Size = new Size(1930, 843);
            splitContainer_big.SplitterDistance = 406;
            splitContainer_big.SplitterWidth = 10;
            splitContainer_big.TabIndex = 0;
            // 
            // splitContainer1
            // 
            splitContainer1.Dock = DockStyle.Fill;
            splitContainer1.FixedPanel = FixedPanel.Panel1;
            splitContainer1.Location = new Point(0, 0);
            splitContainer1.Name = "splitContainer1";
            // 
            // splitContainer1.Panel1
            // 
            splitContainer1.Panel1.Controls.Add(listView_fileList);
            // 
            // splitContainer1.Panel2
            // 
            splitContainer1.Panel2.Controls.Add(splitContainer2);
            splitContainer1.Size = new Size(1930, 406);
            splitContainer1.SplitterDistance = 273;
            splitContainer1.TabIndex = 2;
            // 
            // listView_fileList
            // 
            listView_fileList.AllowColumnReorder = true;
            listView_fileList.AutoArrange = false;
            listView_fileList.Dock = DockStyle.Fill;
            listView_fileList.Location = new Point(0, 0);
            listView_fileList.MultiSelect = false;
            listView_fileList.Name = "listView_fileList";
            listView_fileList.Size = new Size(273, 406);
            listView_fileList.TabIndex = 2;
            listView_fileList.UseCompatibleStateImageBehavior = false;
            listView_fileList.View = View.Details;
            listView_fileList.DoubleClick += listView_fileList_DoubleClick;
            listView_fileList.KeyDown += listView_fileList_KeyDown;
            // 
            // splitContainer2
            // 
            splitContainer2.Dock = DockStyle.Fill;
            splitContainer2.FixedPanel = FixedPanel.Panel1;
            splitContainer2.Location = new Point(0, 0);
            splitContainer2.Name = "splitContainer2";
            // 
            // splitContainer2.Panel1
            // 
            splitContainer2.Panel1.Controls.Add(listView_stepList);
            // 
            // splitContainer2.Panel2
            // 
            splitContainer2.Panel2.Controls.Add(splitContainer3);
            splitContainer2.Size = new Size(1653, 406);
            splitContainer2.SplitterDistance = 798;
            splitContainer2.TabIndex = 0;
            // 
            // listView_stepList
            // 
            listView_stepList.Dock = DockStyle.Fill;
            listView_stepList.Location = new Point(0, 0);
            listView_stepList.Name = "listView_stepList";
            listView_stepList.Size = new Size(798, 406);
            listView_stepList.TabIndex = 3;
            listView_stepList.UseCompatibleStateImageBehavior = false;
            listView_stepList.View = View.Details;
            listView_stepList.SelectedIndexChanged += listView_stepList_SelectedIndexChanged;
            // 
            // splitContainer3
            // 
            splitContainer3.Dock = DockStyle.Fill;
            splitContainer3.FixedPanel = FixedPanel.Panel1;
            splitContainer3.Location = new Point(0, 0);
            splitContainer3.Name = "splitContainer3";
            splitContainer3.Orientation = Orientation.Horizontal;
            // 
            // splitContainer3.Panel1
            // 
            splitContainer3.Panel1.Controls.Add(dataGridView_Action);
            splitContainer3.Panel1.Controls.Add(toolStrip1);
            // 
            // splitContainer3.Panel2
            // 
            splitContainer3.Panel2.Controls.Add(splitContainer4);
            splitContainer3.Size = new Size(851, 406);
            splitContainer3.SplitterDistance = 136;
            splitContainer3.TabIndex = 0;
            // 
            // dataGridView_Action
            // 
            dataGridView_Action.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            dataGridView_Action.Dock = DockStyle.Fill;
            dataGridView_Action.EditMode = DataGridViewEditMode.EditProgrammatically;
            dataGridView_Action.Location = new Point(0, 28);
            dataGridView_Action.MultiSelect = false;
            dataGridView_Action.Name = "dataGridView_Action";
            dataGridView_Action.RowHeadersVisible = false;
            dataGridView_Action.RowHeadersWidth = 51;
            dataGridView_Action.ShowCellErrors = false;
            dataGridView_Action.ShowCellToolTips = false;
            dataGridView_Action.ShowEditingIcon = false;
            dataGridView_Action.ShowRowErrors = false;
            dataGridView_Action.Size = new Size(851, 108);
            dataGridView_Action.TabIndex = 0;
            // 
            // toolStrip1
            // 
            toolStrip1.ImageScalingSize = new Size(20, 20);
            toolStrip1.Items.AddRange(new ToolStripItem[] { toolStripLabel1 });
            toolStrip1.Location = new Point(0, 0);
            toolStrip1.Name = "toolStrip1";
            toolStrip1.Size = new Size(851, 28);
            toolStrip1.TabIndex = 1;
            toolStrip1.Text = "toolStrip1";
            // 
            // toolStripLabel1
            // 
            toolStripLabel1.Font = new Font("맑은 고딕", 10.8F, FontStyle.Bold, GraphicsUnit.Point, 129);
            toolStripLabel1.Name = "toolStripLabel1";
            toolStripLabel1.Size = new Size(68, 25);
            toolStripLabel1.Text = "Action";
            // 
            // splitContainer4
            // 
            splitContainer4.Dock = DockStyle.Fill;
            splitContainer4.FixedPanel = FixedPanel.Panel1;
            splitContainer4.Location = new Point(0, 0);
            splitContainer4.Name = "splitContainer4";
            splitContainer4.Orientation = Orientation.Horizontal;
            // 
            // splitContainer4.Panel1
            // 
            splitContainer4.Panel1.Controls.Add(dataGridView_Transport);
            splitContainer4.Panel1.Controls.Add(toolStrip2);
            // 
            // splitContainer4.Panel2
            // 
            splitContainer4.Panel2.Controls.Add(dataGridView_Unit);
            splitContainer4.Panel2.Controls.Add(toolStrip3);
            splitContainer4.Size = new Size(851, 266);
            splitContainer4.SplitterDistance = 162;
            splitContainer4.TabIndex = 0;
            // 
            // dataGridView_Transport
            // 
            dataGridView_Transport.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            dataGridView_Transport.Dock = DockStyle.Fill;
            dataGridView_Transport.EditMode = DataGridViewEditMode.EditProgrammatically;
            dataGridView_Transport.Location = new Point(0, 28);
            dataGridView_Transport.MultiSelect = false;
            dataGridView_Transport.Name = "dataGridView_Transport";
            dataGridView_Transport.RowHeadersVisible = false;
            dataGridView_Transport.RowHeadersWidth = 51;
            dataGridView_Transport.ShowCellErrors = false;
            dataGridView_Transport.ShowCellToolTips = false;
            dataGridView_Transport.ShowEditingIcon = false;
            dataGridView_Transport.ShowRowErrors = false;
            dataGridView_Transport.Size = new Size(851, 134);
            dataGridView_Transport.TabIndex = 1;
            // 
            // toolStrip2
            // 
            toolStrip2.ImageScalingSize = new Size(20, 20);
            toolStrip2.Items.AddRange(new ToolStripItem[] { toolStripLabel2 });
            toolStrip2.Location = new Point(0, 0);
            toolStrip2.Name = "toolStrip2";
            toolStrip2.Size = new Size(851, 28);
            toolStrip2.TabIndex = 2;
            toolStrip2.Text = "toolStrip2";
            // 
            // toolStripLabel2
            // 
            toolStripLabel2.Font = new Font("맑은 고딕", 10.8F, FontStyle.Bold, GraphicsUnit.Point, 129);
            toolStripLabel2.Name = "toolStripLabel2";
            toolStripLabel2.Size = new Size(132, 25);
            toolStripLabel2.Text = "Transport State";
            // 
            // dataGridView_Unit
            // 
            dataGridView_Unit.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            dataGridView_Unit.Dock = DockStyle.Fill;
            dataGridView_Unit.EditMode = DataGridViewEditMode.EditProgrammatically;
            dataGridView_Unit.Location = new Point(0, 28);
            dataGridView_Unit.MultiSelect = false;
            dataGridView_Unit.Name = "dataGridView_Unit";
            dataGridView_Unit.RowHeadersVisible = false;
            dataGridView_Unit.RowHeadersWidth = 51;
            dataGridView_Unit.ShowCellErrors = false;
            dataGridView_Unit.ShowCellToolTips = false;
            dataGridView_Unit.ShowEditingIcon = false;
            dataGridView_Unit.ShowRowErrors = false;
            dataGridView_Unit.Size = new Size(851, 72);
            dataGridView_Unit.TabIndex = 1;
            // 
            // toolStrip3
            // 
            toolStrip3.ImageScalingSize = new Size(20, 20);
            toolStrip3.Items.AddRange(new ToolStripItem[] { toolStripLabel3 });
            toolStrip3.Location = new Point(0, 0);
            toolStrip3.Name = "toolStrip3";
            toolStrip3.Size = new Size(851, 28);
            toolStrip3.TabIndex = 2;
            toolStrip3.Text = "toolStrip3";
            // 
            // toolStripLabel3
            // 
            toolStripLabel3.Font = new Font("맑은 고딕", 10.8F, FontStyle.Bold, GraphicsUnit.Point, 129);
            toolStripLabel3.Name = "toolStripLabel3";
            toolStripLabel3.Size = new Size(98, 25);
            toolStripLabel3.Text = "Unit State";
            // 
            // statusStrip1
            // 
            statusStrip1.ImageScalingSize = new Size(20, 20);
            statusStrip1.Items.AddRange(new ToolStripItem[] { toolStripStatusLabel_reward, toolStripStatusLabel_totalStep, toolStripStatusLabel_curr_time });
            statusStrip1.Location = new Point(0, 871);
            statusStrip1.Name = "statusStrip1";
            statusStrip1.Size = new Size(1930, 26);
            statusStrip1.TabIndex = 1;
            statusStrip1.Text = "statusStrip1";
            // 
            // toolStripStatusLabel_reward
            // 
            toolStripStatusLabel_reward.Name = "toolStripStatusLabel_reward";
            toolStripStatusLabel_reward.Size = new Size(91, 20);
            toolStripStatusLabel_reward.Text = "total reward";
            // 
            // toolStripStatusLabel_totalStep
            // 
            toolStripStatusLabel_totalStep.Name = "toolStripStatusLabel_totalStep";
            toolStripStatusLabel_totalStep.Size = new Size(73, 20);
            toolStripStatusLabel_totalStep.Text = "total step";
            // 
            // toolStripStatusLabel_curr_time
            // 
            toolStripStatusLabel_curr_time.Name = "toolStripStatusLabel_curr_time";
            toolStripStatusLabel_curr_time.Size = new Size(92, 20);
            toolStripStatusLabel_curr_time.Text = "current time";
            // 
            // menuStrip1
            // 
            menuStrip1.ImageScalingSize = new Size(20, 20);
            menuStrip1.Items.AddRange(new ToolStripItem[] { fileToolStripMenuItem, infoToolStripMenuItem });
            menuStrip1.Location = new Point(0, 0);
            menuStrip1.Name = "menuStrip1";
            menuStrip1.Size = new Size(1930, 28);
            menuStrip1.TabIndex = 0;
            menuStrip1.Text = "menuStrip1";
            // 
            // fileToolStripMenuItem
            // 
            fileToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { menu_selectDirecotry, menu_clear, menu_exit });
            fileToolStripMenuItem.Name = "fileToolStripMenuItem";
            fileToolStripMenuItem.Size = new Size(46, 24);
            fileToolStripMenuItem.Text = "File";
            // 
            // menu_selectDirecotry
            // 
            menu_selectDirecotry.Name = "menu_selectDirecotry";
            menu_selectDirecotry.Size = new Size(198, 26);
            menu_selectDirecotry.Text = "Select Direcotry";
            menu_selectDirecotry.Click += menu_selectDirecotry_Click;
            // 
            // menu_clear
            // 
            menu_clear.Name = "menu_clear";
            menu_clear.Size = new Size(198, 26);
            menu_clear.Text = "Clear";
            // 
            // menu_exit
            // 
            menu_exit.Name = "menu_exit";
            menu_exit.Size = new Size(198, 26);
            menu_exit.Text = "Exit";
            // 
            // infoToolStripMenuItem
            // 
            infoToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { menu_logInfo });
            infoToolStripMenuItem.Name = "infoToolStripMenuItem";
            infoToolStripMenuItem.Size = new Size(50, 24);
            infoToolStripMenuItem.Text = "Info";
            // 
            // menu_logInfo
            // 
            menu_logInfo.Name = "menu_logInfo";
            menu_logInfo.Size = new Size(149, 26);
            menu_logInfo.Text = "Log Info";
            // 
            // timer1
            // 
            timer1.Enabled = true;
            timer1.Tick += timer1_Tick;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(9F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1930, 897);
            Controls.Add(panel1);
            Name = "Form1";
            Text = "Step Log Viewer";
            Load += Form1_Load;
            panel1.ResumeLayout(false);
            panel1.PerformLayout();
            splitContainer_big.Panel1.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)splitContainer_big).EndInit();
            splitContainer_big.ResumeLayout(false);
            splitContainer1.Panel1.ResumeLayout(false);
            splitContainer1.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)splitContainer1).EndInit();
            splitContainer1.ResumeLayout(false);
            splitContainer2.Panel1.ResumeLayout(false);
            splitContainer2.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)splitContainer2).EndInit();
            splitContainer2.ResumeLayout(false);
            splitContainer3.Panel1.ResumeLayout(false);
            splitContainer3.Panel1.PerformLayout();
            splitContainer3.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)splitContainer3).EndInit();
            splitContainer3.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)dataGridView_Action).EndInit();
            toolStrip1.ResumeLayout(false);
            toolStrip1.PerformLayout();
            splitContainer4.Panel1.ResumeLayout(false);
            splitContainer4.Panel1.PerformLayout();
            splitContainer4.Panel2.ResumeLayout(false);
            splitContainer4.Panel2.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)splitContainer4).EndInit();
            splitContainer4.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)dataGridView_Transport).EndInit();
            toolStrip2.ResumeLayout(false);
            toolStrip2.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)dataGridView_Unit).EndInit();
            toolStrip3.ResumeLayout(false);
            toolStrip3.PerformLayout();
            statusStrip1.ResumeLayout(false);
            statusStrip1.PerformLayout();
            menuStrip1.ResumeLayout(false);
            menuStrip1.PerformLayout();
            ResumeLayout(false);
        }

        #endregion

        private Panel panel1;
        private SplitContainer splitContainer1;
        private SplitContainer splitContainer_big;
        private ListView listView_fileList;
        private SplitContainer splitContainer2;
        private ListView listView_stepList;
        private SplitContainer splitContainer3;
        private DataGridView dataGridView_Action;
        private SplitContainer splitContainer4;
        private DataGridView dataGridView_Transport;
        private DataGridView dataGridView_Unit;
        private StatusStrip statusStrip1;
        private ToolStripStatusLabel toolStripStatusLabel_reward;
        private MenuStrip menuStrip1;
        private ToolStripMenuItem fileToolStripMenuItem;
        private ToolStripMenuItem menu_selectDirecotry;
        private ToolStripMenuItem menu_clear;
        private ToolStripMenuItem menu_exit;
        private ToolStripMenuItem infoToolStripMenuItem;
        private ToolStripMenuItem menu_logInfo;
        private ToolStripStatusLabel toolStripStatusLabel_totalStep;
        private ToolStrip toolStrip1;
        private ToolStrip toolStrip2;
        private ToolStrip toolStrip3;
        private ToolStripLabel toolStripLabel1;
        private ToolStripLabel toolStripLabel2;
        private ToolStripLabel toolStripLabel3;
        private ToolStripStatusLabel toolStripStatusLabel_curr_time;
        private System.Windows.Forms.Timer timer1;
    }
}
