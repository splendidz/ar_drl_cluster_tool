using System;
using System.Collections.Generic;
using System.ComponentModel.Design;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StepLogViewer
{
    namespace TensorFieldMap
    {
        public enum Unit
        {
            REQUIRED_TIMESTEP = 0
            , CURR_WAFER_WAYPOINT
            , READY_TO_PICK
            , READY_TO_PLACE
            , WAFER_ID
            // , WAFER_COUNT
            , POS_X
            , POS_Y
            , POS_Z

            , LENGTH
        }
        public class OHCommandType
        {
            
            public static string ToString(int value)
            {
                
                switch (value)
                {
                    case 0: return "noop";
                    case 1: return "pick";
                    case 2: return "place";
                    case 3: return "move";
                    default:
                        return "unknown";
                }
            }
            public static string ToString(double[] oh) 
            {
                if (oh.Length != 4)
                    return "";
                if (oh[0] == 1 && oh[1] == 0 && oh[2] == 0 && oh[3] == 0)
                    return "noop";
                else if (oh[0] == 0 && oh[1] == 1 && oh[2] == 0 && oh[3] == 0)
                    return "pick";
                else if (oh[0] == 0 && oh[1] == 0 && oh[2] == 1 && oh[3] == 0)
                    return "place";
                else if (oh[0] == 0 && oh[1] == 0 && oh[2] == 0 && oh[3] == 1)
                    return "move";
                return "unknown";
            }
        }

        public enum Transport
        {
            SET_ACTION_FLAG = 0
            , REQUIRED_TIMESTEP 

            // current action
            , OH_CMD_TYPE_NOOP  // OneHot
            , OH_CMD_TYPE_PICK   // OneHot
            , OH_CMD_TYPE_PLACE  // OneHot
            , OH_CMD_TYPE_MOVE  // OneHot
            , CMD_TARGET_POS_X
            , CMD_TARGET_POS_Y
            , CMD_TARGET_POS_Z

            // current pos and status
            , CURRENT_POS_X
            , CURRENT_POS_Y
            , CURRENT_POS_Z
            , READY_TO_PICK_ARM_1
            , READY_TO_PICK_ARM_2
            , READY_TO_PLACE_ARM_1
            , READY_TO_PLACE_ARM_2
            , CURRENT_WAFER_WAYPOINT_ARM_1
            , CURRENT_WAFER_WAYPOINT_ARM_2
            , WAFER_ID_ARM1
            , WAFER_ID_ARM2
            , LENGTH
        }
    }
}
