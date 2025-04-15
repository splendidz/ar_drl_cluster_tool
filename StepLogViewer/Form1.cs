using StepLogViewer.TensorFieldMap;
using System;
using System.Reflection;
using System.Security.Cryptography;
using System.Security.Cryptography.Xml;
using System.Windows.Forms;
using System.Xml.Linq;
using System.Xml.Serialization;
using static System.Runtime.InteropServices.JavaScript.JSType;
using static System.Windows.Forms.VisualStyles.VisualStyleElement;

namespace StepLogViewer
{
    public partial class Form1 : Form
    {
        public class TimeDuration
        {
            public bool workingFlag = false;
            public bool hasWafer = false;
            public double startTime = 0;
            public double endTime = 0;
            public double scalarValue = double.MinValue;
            public double Duration { get { return endTime - startTime; } }
        }

        private GanttChartControl ganttChart = new GanttChartControl();
        LogParser currentLog = new LogParser();
        string currentDirecotry = "";
        const string TITLE = "Step Log Veiwer";
        public Form1()
        {
            InitializeComponent();

            // 
            // timelineChart
            // 
            splitContainer_big.Panel2.Controls.Add(ganttChart);
            ganttChart.ClientSize = new Size(1029, 600);
            ganttChart.Location = new Point(0, 0);
            ganttChart.Margin = new Padding(0);
            ganttChart.Name = "timelineChart";
            ganttChart.Text = "UTimelineChart";
            ganttChart.Dock = DockStyle.Fill;
            ganttChart.Visible = true;


            // File List : Add columns to ListView
            listView_fileList.Columns.Add("File Name", 150);
            listView_fileList.Columns.Add("Size (bytes)", 120);
            listView_fileList.FullRowSelect = true;
            listView_fileList.GridLines = true;

            listView_stepList.Columns.Add("No", 40);
            listView_stepList.Columns.Add("Timestep", 90);
            listView_stepList.Columns.Add("RequiredTime", 130);
            listView_stepList.Columns.Add("i_act", 70);
            listView_stepList.Columns.Add("Action", 260);
            listView_stepList.Columns.Add("Error", 100);
            listView_stepList.Columns.Add("Reward", 80);
            listView_stepList.Columns.Add("Reward Sum", 110);
            //listView_stepList.Columns.Add("Comment", 200);
            listView_stepList.FullRowSelect = true;
            listView_stepList.GridLines = true;

            // Action Grid: Add columns
            //dataGridView_Action.Columns.Add("transport id", "transport id"); // String column
            dataGridView_Action.Columns.Add("transport", "transport"); // String column
            dataGridView_Action.Columns.Add("action", "action"); // String column
            dataGridView_Action.Columns.Add("arm id", "arm id"); // Int column
            //dataGridView_Action.Columns.Add("unit id", "unit id");     // String column
            dataGridView_Action.Columns.Add("unit", "unit");     // String column

            // Tranfer Grid: Add columns
            //dataGridView_Transport.Columns.Add("id", "id"); 
            dataGridView_Transport.Columns.Add("name", "name");
            dataGridView_Transport.Columns.Add("set action", "set action");
            dataGridView_Transport.Columns.Add("left timestep", "left timestep");
            dataGridView_Transport.Columns.Add("curr_act_cmd", "curr_act_cmd");
            //dataGridView_Transport.Columns.Add("act_arm", "act_arm");
            dataGridView_Transport.Columns.Add("curr_act_target_pos", "curr_act_target_pos");
            //dataGridView_Transport.Columns.Add("act_target_unit_name", "act_target_unit_name");
            dataGridView_Transport.Columns.Add("curent pos", "curent pos");
            dataGridView_Transport.Columns.Add("ready to pick", "ready to pick");
            dataGridView_Transport.Columns.Add("ready to place", "ready to place");
            dataGridView_Transport.Columns.Add("curr waypoint", "curr waypoint");
            dataGridView_Transport.Columns.Add("wafer id", "wafer id");

            // Unit Grid: Add columns
            dataGridView_Unit.Columns.Add("name", "name");
            dataGridView_Unit.Columns.Add("timestep", "timestep");
            dataGridView_Unit.Columns.Add("wafer id", "wafer id");
            //dataGridView_Unit.Columns.Add("wafer count", "wafer count");
            dataGridView_Unit.Columns.Add("curr waypoint", "waypoint");
            dataGridView_Unit.Columns.Add("ready to pick", "ready to pick");
            dataGridView_Unit.Columns.Add("ready to place", "ready to place");
            dataGridView_Unit.Columns.Add("pos", "pos");

            dataGridView_Action.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.AllCells;
            dataGridView_Transport.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.AllCells;
            dataGridView_Unit.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.AllCells;
            ganttChart.SetTimeChangeEvent(listview_DoChangeSelect);

            this.Text = TITLE;
        }
        public string ListToString<T>(List<T> list, string name)
        {
            List<string> strList = new List<string>();
            foreach (T item in list)
            {
                strList.Add(string.Format($"{name}[{strList.Count + 1}]: {item.ToString()}"));
            }
            return strList.Count > 0 ? string.Join(", ", strList) : "Empty";
        }

        private void menu_selectDirecotry_Click(object sender, EventArgs e)
        {
            // Open a FolderBrowserDialog to select a folder
            using (FolderBrowserDialog folderDialog = new FolderBrowserDialog())
            {
                if (folderDialog.ShowDialog() == DialogResult.OK)
                {
                    currentDirecotry = folderDialog.SelectedPath;
                    // Get all files in the selected folder
                    string[] files = Directory.GetFiles(folderDialog.SelectedPath);

                    // Clear existing items in the ListView
                    listView_fileList.Items.Clear();

                    // Add files to the ListView
                    foreach (string file in files)
                    {
                        FileInfo fileInfo = new FileInfo(file);
                        if (Path.GetExtension(fileInfo.Name) != ".dat")
                            continue;
                        var listViewItem = new ListViewItem(fileInfo.Name);
                        listViewItem.SubItems.Add(fileInfo.Length.ToString());
                        listView_fileList.Items.Add(listViewItem);
                    }
                }
            }
            this.Text = TITLE;
        }
        private void OpenStepLogFile(string path)
        {
            try
            {
                this.currentLog = new LogParser();
                this.currentLog.ParseFile(path);
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                this.Text = TITLE;
                return;
            }
            this.Text = TITLE + " - " + Path.GetFileName(path);
            dataGridView_Action.Rows.Clear();
            dataGridView_Action.Rows.Clear();

            listView_stepList.Items.Clear();
            int i = 1;
            double lastTimestep = 0;
            foreach (var stepData in currentLog.EpisodeData)
            {

                var listViewItem = new ListViewItem(Convert.ToString(i));
                //listViewItem.SubItems.Add(i.ToString());
                lastTimestep = Math.Round(stepData.total_timestep, 3);
                listViewItem.SubItems.Add(Math.Round(stepData.total_timestep, 3).ToString());
                listViewItem.SubItems.Add(stepData.timestep.ToString());
                listViewItem.SubItems.Add(stepData.receivedAction.i_action.ToString());
                listViewItem.SubItems.Add(stepData.receivedAction.ToString());
                listViewItem.SubItems.Add(stepData.error);
                listViewItem.SubItems.Add(stepData.reward.ToString());
                listViewItem.SubItems.Add(stepData.reward_sum.ToString());
                listView_stepList.Items.Add(listViewItem);
                i++;
            }

            var lastObj = currentLog.EpisodeData[currentLog.EpisodeData.Count - 1];


            toolStripStatusLabel_reward.Text = "Total Reward: " + lastObj.reward_sum.ToString();
            toolStripStatusLabel_totalStep.Text = "Total Step: " + lastTimestep.ToString();
            GenerateGanttChatData();
            ganttChart.InvokeDraw();

        }


        private void GenerateGanttChatData()
        {
            ganttChart.Clear();
            Dictionary<string, List<TimeDuration>> timeDataDict = new Dictionary<string, List<TimeDuration>>();
            timeDataDict["Reward"] = new List<TimeDuration>();
            ganttChart.AddField(GanttType.scalar_field, "Reward");

            foreach (var transport in this.currentLog.InfoData.transports)
            {
                for (int aid = 0; aid < transport.ArmCount; aid++)
                {
                    string name = $"{transport.Name}.Arm{aid + 1}";
                    ganttChart.AddField(GanttType.bool_field, name);
                    timeDataDict[name] = new List<TimeDuration>();
                }
            }
            foreach (var unit in this.currentLog.InfoData.units)
            {
                ganttChart.AddField(GanttType.bool_field, $"{unit.Name}");
                timeDataDict[$"{unit.Name}"] = new List<TimeDuration>();
            }


            for (int i = 0; i < currentLog.EpisodeData.Count; i++)
            {
                StepData stepData = currentLog.EpisodeData[i];

                bool skip = false;
                for (int t=0;t< stepData.transportStateList.Count;t++) 
                {
                    if (stepData.transportStateList[t].setActionFlag)
                    {
                        skip = true;
                        break;
                    }
                }
                if (skip)
                    continue;

                for (int tid = 0; tid < currentLog.InfoData.transports.Count; tid++)
                {
                    for (int aid = 0; aid < currentLog.InfoData.transports[tid].ArmCount; aid++)
                    {
                        string name = $"{currentLog.InfoData.transports[tid].Name}.Arm{aid + 1}";
                        List<TimeDuration> listData = timeDataDict[name];
                        listData.Add(new TimeDuration { workingFlag = false/*stepData.transportStateList[tid].leftTimeStep > 0*/, hasWafer = stepData.transportStateList[tid].currentWaypoint[aid] > 0, startTime = stepData.total_timestep });
                    }
                }

                for (int uid = 0; uid < currentLog.InfoData.units.Count; uid++)
                {
                    string name = $"{currentLog.InfoData.units[uid].Name}";
                    List<TimeDuration> listData = timeDataDict[name];
                    listData.Add(new TimeDuration { workingFlag = stepData.unitStateList[uid].leftTimeStep > 0, hasWafer = stepData.unitStateList[uid].currWaypoint > 0 || stepData.unitStateList[uid].readyToPick, startTime = stepData.total_timestep });
                }
                if (true)
                {
                    List<TimeDuration> listData = timeDataDict["Reward"];
                    listData.Add(new TimeDuration { scalarValue = stepData.reward, startTime = stepData.total_timestep });
                }
            }

            foreach (var dataList in timeDataDict)
            {
                List<TimeDuration> timeDurations = new List<TimeDuration>();
                double lastTime = 0;
                foreach (var data in dataList.Value)
                {
                    if (data.scalarValue != double.MinValue)
                    {
                        timeDurations.Add(data);
                        continue;
                    }

                    bool needToMake = data.hasWafer || data.workingFlag;
                    if (timeDurations.Count() == 0)
                    {
                        if (needToMake)
                            timeDurations.Add(data);
                        continue;
                    }
                    bool diffData = timeDurations.Last().hasWafer != data.hasWafer || timeDurations.Last().workingFlag != data.workingFlag;

                    if (diffData)
                    {
                        if (timeDurations.Last().endTime == 0)
                            timeDurations.Last().endTime = data.startTime;

                        //if (needToMake)
                        {
                            timeDurations.Add(data);
                            //continue;
                        }
                    }
                    lastTime = data.startTime;
                }
                if (timeDurations.Count() > 0 && timeDurations.Last().endTime == 0)
                    timeDurations.Last().endTime = lastTime;

                timeDataDict[dataList.Key] = timeDurations;
            }


            foreach (var dataList in timeDataDict)
            {
                foreach (var data in dataList.Value)
                {
                    if (data.scalarValue == double.MinValue)
                    {
                        if (data.workingFlag || data.hasWafer)
                            ganttChart.AddGanttData(dataList.Key, data.startTime, data.Duration, data.workingFlag);
                    }
                    else
                        ganttChart.AddScalarData(dataList.Key, data.startTime, data.scalarValue);
                }
            }
        }

        private void AddTimeDurationData(List<TimeDuration> listData, double timestep, double leftTime, bool readyToPick)
        {
            bool workingFlag = leftTime > 0;
            if (listData.Count() == 0)
            {
                if (readyToPick || workingFlag)
                {
                    listData.Add(new TimeDuration { startTime = timestep, workingFlag = workingFlag });// new data add
                    return;
                }
            }
            else
            {
                if (listData.Last().workingFlag != workingFlag)
                {
                    listData.Last().endTime = timestep;
                    listData.Add(new TimeDuration { startTime = timestep, workingFlag = workingFlag });// new data add
                }
                else
                    listData.Last().endTime = timestep;
            }
        }
        private void AddTimeDurationData2(List<TimeDuration> listData, double timestep, bool hasWafer)
        {
            if (listData.Count() == 0)
            {
                if (hasWafer)
                {
                    listData.Add(new TimeDuration { startTime = timestep, workingFlag = hasWafer });// new data add
                    return;
                }
            }
            else
            {
                if (hasWafer)
                {
                    listData.Last().endTime = timestep;
                    listData.Add(new TimeDuration { startTime = timestep, workingFlag = hasWafer });// new data add
                }
                else
                    listData.Last().endTime = timestep;
            }
        }
        private void listView_fileList_DoubleClick(object sender, EventArgs e)
        {
            if (listView_fileList.SelectedItems.Count > 0)
            {
                var selectedItem = listView_fileList.SelectedItems[0];
                OpenStepLogFile(Path.Combine(currentDirecotry, selectedItem.SubItems[0].Text));
            }
        }

        private void listView_fileList_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter && listView_fileList.SelectedItems.Count > 0)
            {
                var selectedItem = listView_fileList.SelectedItems[0];
                OpenStepLogFile(Path.Combine(currentDirecotry, selectedItem.SubItems[0].Text));
            }
        }
        bool _changeTriggered_byChart = false;
        private void listview_DoChangeSelect(double dTime)
        {
            int idx = -1;
            for (int i = 0; i < listView_stepList.Items.Count; i++)
            {
                double dCurr = Convert.ToDouble(listView_stepList.Items[i].SubItems[1].Text);
                double dNext = 0;
                if (i + 1 < listView_stepList.Items.Count)
                    dNext = Convert.ToDouble(listView_stepList.Items[i + 1].SubItems[1].Text);


                if (dTime == dCurr)
                {
                    idx = i;
                    break;
                }
                else if (dTime > dCurr && dTime < dNext)
                {
                    idx = i;
                    break;
                }
            }
            if (idx == -1)
                return;

            _changeTriggered_byChart = true;
            listView_stepList.SelectedItems.Clear();
            listView_stepList.Items[idx].Selected = true;
            listView_stepList.Items[idx].Focused = true;
            listView_stepList.EnsureVisible(idx);
        }

        private void listView_stepList_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (listView_stepList.SelectedItems.Count > 0)
            {
                int idx = listView_stepList.SelectedItems[0].Index;
                dataGridView_Action.SuspendLayout();
                dataGridView_Transport.SuspendLayout();
                dataGridView_Unit.SuspendLayout();


                var action_fake_list = new List<SingleAction>();
                action_fake_list.Add(currentLog.EpisodeData[idx].receivedAction);

                UpdateDataGridView(dataGridView_Action, action_fake_list,
                    action => new object[] { action.tr_name, action.action_type, action.arm_index, action.target_name });

                UpdateDataGridView(dataGridView_Transport, currentLog.EpisodeData[idx].transportStateList,
                    transport => new object[] { 
                        transport.trInfo.Name,
                        transport.setActionFlag,
                        transport.leftTimeStep,
                        transport.currentActionType, 
                        transport.currentActionTargetPos.ToString(),
                        transport.currentPos3D.ToString(), 
                        ListToString(transport.readyToPick, "Arm"), 
                        ListToString(transport.readyToPlace, "Arm"), 
                        ListToString(transport.currentWaypoint, "Arm"), 
                        ListToString(transport.WaferID, "Arm")});

                UpdateDataGridView(dataGridView_Unit, currentLog.EpisodeData[idx].unitStateList,
                    unit => new object[] { 
                        unit.unitInfo.Name, 
                        unit.leftTimeStep, 
                        unit.waferID, 
                        //unit.waferCount,
                        unit.currWaypoint, 
                        unit.readyToPick, 
                        unit.readyToPlace, 
                        unit.pos3D.ToString()});

                dataGridView_Action.ResumeLayout();
                dataGridView_Transport.ResumeLayout();
                dataGridView_Unit.ResumeLayout();


                if (_changeTriggered_byChart == false)
                {
                    double newPos_sec = (int)currentLog.EpisodeData[idx].total_timestep - 5;
                    newPos_sec = newPos_sec < 0 ? 0 : newPos_sec;
                    DrawProperties.Inst.xAxisTimeGuidePos_sec = currentLog.EpisodeData[idx].total_timestep;
                    DrawProperties.Inst.HScrollOffset_sec = (int)newPos_sec;// (int)currentLog.EpisodeData[idx].total_timestep;
                                                                            //timelineChart.SetNewHScrollValue((int)newPos_sec);
                    ganttChart.InvokeDraw();
                }
                _changeTriggered_byChart = false;
            }
        }
        private void UpdateDataGridView<T>(DataGridView dataGridView, IEnumerable<T> newData, Func<T, object[]> rowExtractor)
        {
            try
            {
                int rowIndex = 0;

                foreach (var dataItem in newData)
                {
                    var newValues = rowExtractor(dataItem);

                    // If the row already exists, update it
                    if (rowIndex < dataGridView.Rows.Count)
                    {
                        var row = dataGridView.Rows[rowIndex];

                        for (int colIndex = 0; colIndex < newValues.Length; colIndex++)
                        {
                            HighlightIfChanged(row.Cells[colIndex], newValues[colIndex]);
                        }
                    }
                    else
                    {
                        // Add a new row if it doesn't already exist
                        dataGridView.Rows.Add(newValues);
                    }

                    rowIndex++;
                }

                // Remove excess rows if the newData has fewer rows
                while (dataGridView.Rows.Count > rowIndex)
                {
                    dataGridView.Rows.RemoveAt(dataGridView.Rows.Count - 1);
                }
            }
            catch (Exception)
            {

            }
        }

        // Helper method to check for changes and highlight changed cells
        private void HighlightIfChanged(DataGridViewCell cell, object newValue)
        {
            if (!Equals(cell.Value, newValue))
            {
                cell.Value = newValue;

                // Highlight the cell with a special color
                cell.Style.BackColor = Color.Yellow; // Use any color you prefer
            }
            else
            {
                // Reset the cell style if it hasn't changed
                cell.Style.BackColor = Color.White; // Or the default background color
            }
        }

        private void Form1_Load(object sender, EventArgs e)
        {

            ganttChart.Show();
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            toolStripStatusLabel_curr_time.Text = $"Current Time: {Math.Round(DrawProperties.Inst.MouseCurrentTime_sec, 3)}";
        }
    }
}
