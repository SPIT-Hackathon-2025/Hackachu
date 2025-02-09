import { ExternalLink, CheckCircle, Clock } from "lucide-react"
import { motion } from "framer-motion"

const TasksPage = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <h1 className="text-3xl font-bold text-black">Tasks</h1>
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white shadow-lg rounded-lg p-6 space-y-6 border border-indigo-200"
      >
        <a
          href="https://www.notion.so"
          target="_blank"
          rel="noopener noreferrer"
          className="text-black hover:text-indigo-800 flex items-center space-x-2 transition duration-200"
        >
          <ExternalLink size={20} />
          <span>Access current tasks in Notion</span>
        </a>
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-black">Recent Task Activity</h2>
          <div className="space-y-2">
            <p className="text-gray-700 flex items-center space-x-2">
              <CheckCircle size={16} className="text-green-500" />
              <span>Task X was completed 2 hours ago</span>
            </p>
            <p className="text-gray-700 flex items-center space-x-2">
              <Clock size={16} className="text-yellow-500" />
              <span>Task Y was updated 4 hours ago</span>
            </p>
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-black">Task Progress</h2>
          <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
            <motion.div
              className="bg-indigo-600 h-2.5"
              initial={{ width: 0 }}
              animate={{ width: "45%" }}
              transition={{ duration: 1, delay: 0.5 }}
            ></motion.div>
          </div>
          <p className="text-sm text-gray-600">45% of tasks completed</p>
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-black">Pinned Tasks</h2>
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            <li>Important meeting preparation</li>
            <li>Quarterly report draft</li>
          </ul>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default TasksPage

