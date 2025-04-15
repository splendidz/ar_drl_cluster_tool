using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.Security.AccessControl;
using System.Text.Json;
using StepLogViewer.TensorFieldMap;
using System.Security.Cryptography.Xml;
namespace StepLogViewer
{
    class Tools
    {
        public static double[] ExtractTensor(double[] srcArray, int index, int count)
        {
            return (new ArraySegment<double>(srcArray, index, count)).ToArray();
        }
        public static Pos3D ParsePos3D(string positionString)
        {
            var parts = positionString.Split(",");
            return new Pos3D
            {
                x = double.Parse(parts[0].Trim()),
                y = double.Parse(parts[1].Trim()),
                z = double.Parse(parts[2].Trim())
            };
        }
    }
    public class Pos3D
    {
        public double x { get; set; } = 0;
        public double y { get; set; } = 0;
        public double z { get; set; } = 0;

        public override string ToString()
        {
            return String.Format($"{x}, {y}, {z}");
        }
    }

    /// <summary>
    /// 하나의 에피소드 실행 로그 파일 파싱 결과. info.json을 먼저 파싱하고 로딩하고자 하는 에피소드를 파싱한다.
    /// </summary>
    public class LogParser
    {
        private bool _once_loaded = false;
        /// info.json 파일 정보
        public Info InfoData { get; private set; } = new Info();

        /// 모든 스텝에 해당(한 에피소드)
        public List<StepData> EpisodeData { get; private set; } = new List<StepData>();

        public LogParser()
        { 
        }

        public bool ParseFile(string filePath)
        {
            if(_once_loaded) return false;
            _once_loaded = true;

            string infoFilePath = Path.Combine(Path.GetDirectoryName(filePath), "Info.json");
            InfoData.ParseJson(infoFilePath);

            using (StreamReader reader = new StreamReader(filePath))
            {
                string? line;
                while ((line = reader.ReadLine()) != null)
                {
                    if (line.StartsWith("[data]"))
                    {
                        StepData stepData = new StepData();
                        stepData.ParseStepData(InfoData, reader);
                        EpisodeData.Add(stepData);
                    }
                }
            }
            return true;
        }
    }

    /// <summary>
    /// Json Info 파일 파싱 데이터
    /// </summary>
    public class Info
    {
        public int maxArmCount { get; private set; } = 0;
        public double maxProcessTime { get; private set; } = 0;
        public int maxWaypoint { get; private set; } = 0;
        public double posScale { get; private set; } = 1;
        public int unitMaxPadding { get; private set; } = 0;
        public int transportMaxPadding { get; private set; } = 0;
        public List<UnitInfo> units { get; private set; } = new List<UnitInfo>();
        public List<TransportInfo> transports { get; private set; } = new List<TransportInfo>();
        public List<SingleAction> Actions { get; private set; } = new List<SingleAction>();

        public void ParseJson(string filePath)
        {
            string jsonString = File.ReadAllText(filePath);
            var jsonObject = JsonSerializer.Deserialize<JsonElement>(jsonString);

            // Parse Units
            if (jsonObject.TryGetProperty("Args", out var args))
            {
                maxProcessTime = args.GetProperty("max_process_time").GetDouble();
                maxWaypoint = args.GetProperty("max_waypoint").GetInt32();
                posScale = args.GetProperty("pos_scale").GetDouble();
                unitMaxPadding = args.GetProperty("unit_max_padding").GetInt32();
                transportMaxPadding = args.GetProperty("transport_max_padding").GetInt32();
            }

            // Parse Units
            if (jsonObject.TryGetProperty("Units", out var unitsElement))
            {
                foreach (var unit in unitsElement.EnumerateObject())
                {
                    var unitData = unit.Value;
                    var unitInfo = new UnitInfo
                    {
                        Id = unitData.GetProperty("ID").GetInt32(),
                        Name = unitData.GetProperty("Name").GetString(),
                        Type = unitData.GetProperty("Type").GetString(),
                        // Capacity = unitData.GetProperty("Capacity").GetInt32(),
                        ProcessTime = unitData.GetProperty("ProcessTime").GetDouble(),
                        pos3D = Tools.ParsePos3D(unitData.GetProperty("Position").GetString())
                    };
                    units.Add(unitInfo);
                }
            }

            // Parse Transports
            if (jsonObject.TryGetProperty("Transports", out var transportsElement))
            {
                foreach (var transport in transportsElement.EnumerateObject())
                {
                    var transportData = transport.Value;
                    var transportInfo = new TransportInfo
                    {
                        Id = transportData.GetProperty("ID").GetInt32(),
                        Name = transportData.GetProperty("Name").GetString(),
                        ArmCount = transportData.GetProperty("ArmCount").GetInt32(),
                        Speed = transportData.GetProperty("Speed").GetDouble()
                    };
                    transports.Add(transportInfo);
                }
            }

            // Parse Actions
            if (jsonObject.TryGetProperty("Actions", out var actionsElement))
            {
                foreach (var actionGroup in actionsElement.EnumerateObject())
                {
                    var actionData = actionGroup.Value;
                    var singleAction = new SingleAction
                    {
                        i_action = int.Parse(actionGroup.Name),
                        tr_name = actionData.GetProperty("tr_name").GetString(),
                        action_type = actionData.GetProperty("command").GetString(),
                        arm_index = actionData.GetProperty("arm_index").GetInt32(),
                        target_name = actionData.GetProperty("target_name").GetString()
                    };

                    Actions.Add(singleAction);
                }
            }
        }
    }
    /// <summary>
    /// 에피소드 실행 로그 파일 파싱 데이터 (한 스텝에 해당)
    /// </summary>
    public class StepData
    {
        public double timestep { get; private set; }
        public double total_timestep { get; private set; }
        public SingleAction receivedAction { get; private set; } = new SingleAction();
        public string error { get; private set; } = string.Empty;
        public double reward { get; private set; }
        public double reward_sum { get; private set; }
        public bool done { get; private set; }
        public string tensor { get; private set; } = string.Empty;

        public List<UnitState> unitStateList { get; private set; } = new List<UnitState> { };
        public List<TransportState> transportStateList { get; private set; } = new List<TransportState> { };

        public void ParseStepData(Info infoData, StreamReader reader)
        {
            string? line;
            while (!string.IsNullOrWhiteSpace(line = reader.ReadLine()))
            {
                int pos = line.IndexOf(':');
                string key = line.Substring(0, pos).Trim();
                string value = line.Substring(pos + 1, line.Length - pos - 1).Trim();

                switch (key)
                {
                    case "timestep":
                        timestep = double.Parse(value);
                        break;
                    case "total_timestep":
                        total_timestep = double.Parse(value);
                        break;
                    case "i_action":
                        int i_action = int.Parse(value);
                        receivedAction = infoData.Actions[i_action];
                        break;
                    case "error":
                        error = value;
                        break;
                    case "reward":
                        reward = String.IsNullOrEmpty(value) ? 0 : double.Parse(value);
                        break;
                    case "reward_sum":
                        reward_sum = String.IsNullOrEmpty(value) ? 0 : double.Parse(value);
                        reward_sum = Math.Round(reward_sum, 2);
                        break;
                    case "done":
                        done = value == "True";
                        break;
                    case "state":
                        tensor = value;
                        break;
                }
            }

            ParsingStateTensor(infoData);
        }
       
        private void ParsingStateTensor(Info infoData)
        {
            double[] elementArray = tensor.Trim('[', ']').Split(',').Select(double.Parse).ToArray();

            List<double[]> transportsTensor = new List<double[]>();
            List<double[]> unitsTensor = new List<double[]>();
            double timestep = 0;
            int offset = 0;
            int i = 0;
            for (i = 0; i < infoData.unitMaxPadding; i++) //InfoFile.units.Count
            {
                unitsTensor.Add(Tools.ExtractTensor(elementArray, offset, (int)TensorFieldMap.Unit.LENGTH));
                offset += (int)TensorFieldMap.Unit.LENGTH;
            }
            for (i = 0; i<infoData.transportMaxPadding; i++) //infoData.transports.Count
            {
                transportsTensor.Add(Tools.ExtractTensor(elementArray, offset, (int)TensorFieldMap.Transport.LENGTH));
                offset += (int)TensorFieldMap.Transport.LENGTH;
            }
            timestep = elementArray[offset++] * 1000;

            if (offset != elementArray.Length)
                throw new Exception("???");

            int id = 0;
            foreach (var unitTensor in unitsTensor)
            {
                var unit = new UnitState();
                unitStateList.Add(unit);

                unit.id = id;
                unit.unitInfo = infoData.units[id];
                unit.leftTimeStep = Math.Round(unitTensor[(int)TensorFieldMap.Unit.REQUIRED_TIMESTEP] * infoData.maxProcessTime, 3);
                unit.currWaypoint = (int)Math.Round(unitTensor[(int)TensorFieldMap.Unit.CURR_WAFER_WAYPOINT] * infoData.maxWaypoint);
                unit.readyToPick = unitTensor[(int)TensorFieldMap.Unit.READY_TO_PICK] != 0;
                unit.readyToPlace = unitTensor[(int)TensorFieldMap.Unit.READY_TO_PLACE] != 0;
                unit.pos3D.x = Math.Round(unitTensor[(int)TensorFieldMap.Unit.POS_X] / infoData.posScale, 0);
                unit.pos3D.y = Math.Round(unitTensor[(int)TensorFieldMap.Unit.POS_Y] / infoData.posScale, 0);
                unit.pos3D.z = Math.Round(unitTensor[(int)TensorFieldMap.Unit.POS_Z] / infoData.posScale, 0);
                unit.waferID = (int)Math.Round(unitTensor[(int)TensorFieldMap.Unit.WAFER_ID] * 1000, 0);
                //unit.waferCount = (int)Math.Round(unitTensor[(int)TensorFieldMap.Unit.WAFER_COUNT] * 1000, 0);

                id++;
            }
            id = 0;
            foreach (var transportTensor in transportsTensor)
            {
                double[] commandOH = Tools.ExtractTensor(transportTensor, (int)TensorFieldMap.Transport.OH_CMD_TYPE_NOOP, 4);
                double[] targetPosXYZ = Tools.ExtractTensor(transportTensor, (int)TensorFieldMap.Transport.CMD_TARGET_POS_X, 3);

                var tr = new TransportState();
                transportStateList.Add(tr);
                tr.id = id;
                tr.trInfo = infoData.transports[id];
                tr.setActionFlag = transportTensor[(int)TensorFieldMap.Transport.SET_ACTION_FLAG] == 1;
                tr.leftTimeStep = Math.Round(transportTensor[(int)TensorFieldMap.Transport.REQUIRED_TIMESTEP] * infoData.maxProcessTime, 3);
                tr.currentActionType = OHCommandType.ToString(commandOH);
                tr.currentActionTargetPos.x = Math.Round(targetPosXYZ[0] / infoData.posScale, 0);
                tr.currentActionTargetPos.y = Math.Round(targetPosXYZ[1] / infoData.posScale, 0);
                tr.currentActionTargetPos.z = Math.Round(targetPosXYZ[2] / infoData.posScale, 0);
                tr.currentPos3D.x = Math.Round(transportTensor[(int)TensorFieldMap.Transport.CURRENT_POS_X] / infoData.posScale, 0);
                tr.currentPos3D.y = Math.Round(transportTensor[(int)TensorFieldMap.Transport.CURRENT_POS_Y] / infoData.posScale, 0);
                tr.currentPos3D.z = Math.Round(transportTensor[(int)TensorFieldMap.Transport.CURRENT_POS_Z] / infoData.posScale, 0);
                for (int j = 0; j < tr.trInfo.ArmCount; j++)
                {
                    tr.readyToPick.Add(transportTensor[(int)TensorFieldMap.Transport.READY_TO_PICK_ARM_1+ j] != 0);
                    tr.readyToPlace.Add(transportTensor[(int)TensorFieldMap.Transport.READY_TO_PLACE_ARM_1+ j] != 0);
                    tr.currentWaypoint.Add((int)Math.Round(transportTensor[(int)TensorFieldMap.Transport.CURRENT_WAFER_WAYPOINT_ARM_1 + j] * infoData.maxWaypoint));
                    tr.WaferID.Add((int)Math.Round(transportTensor[(int)TensorFieldMap.Transport.WAFER_ID_ARM1 + j] * 1000));
                }
                id++;
            }
        }
    }

   

    public class UnitState
    {
        public int id { get; set; } = 0;
        public int waferID { get; set; } = 0;
        // public int waferCount { get; set; } = 0;
        public UnitInfo unitInfo { get; set; } = new UnitInfo();
        public double leftTimeStep { get; set; } = 0;
        public int currWaypoint { get; set; } = 0;
        public bool readyToPick { get; set; } = false;
        public bool readyToPlace { get; set; } = false;

        public Pos3D pos3D { get; set; } = new Pos3D();
    }
    public class TransportState
    {
        public bool setActionFlag { get; set; } = false;
        public int id { get; set; } = 0;
        public TransportInfo trInfo { get; set; } = new TransportInfo();
        public double leftTimeStep { get; set; } = 0;
        public string currentActionType{ get; set; } = string.Empty;
        public Pos3D currentActionTargetPos{ get; set; } = new Pos3D();

        public Pos3D currentPos3D { get; set; } = new Pos3D();
        public List<bool> readyToPick { get; set; } = new List<bool> { };
        public List<bool> readyToPlace { get; set; } = new List<bool> { };
        public List<int> currentWaypoint { get; set; } = new List<int> { };
        public List<int> WaferID { get; set; } = new List<int> { };
    }

    public class SingleAction
    {
        public int i_action { get; set; } = 0;
        public string tr_name { get; set; } = string.Empty;
        public string action_type { get; set; } = string.Empty;
        public int arm_index { get; set; }
        public string target_name { get; set; } = string.Empty;

        public override string ToString()
        {
            return string.Format($"{tr_name}.{arm_index}, {action_type}, {target_name}");
        }
    }

    public class TransportInfo
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public int ArmCount { get; set; }
        public double Speed { get; set; }
    }

    public class UnitInfo
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        //public int Capacity { get; set; }
        public double ProcessTime { get; set; }
        public Pos3D pos3D { get; set; } = new Pos3D();

    }

}