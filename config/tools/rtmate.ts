import { tool } from "@opencode-ai/plugin"
import { execSync } from "child_process"
import { readFileSync, existsSync } from "fs"
import { join } from "path"
import DESCRIPTION from "./rtmate.txt"

/**
 * rtmate - Remote execution with live terminal viewing via tmate
 * 
 * This tool allows the agent to:
 * - Initialize tmate sessions on remote servers
 * - Execute commands with stdout + mirroring to tmate
 * - Send commands to tmate sessions for interactive viewing
 */

// Tool version for debugging
const TOOL_VERSION = "1.0.0-fix-split-20260127"

// Helper to get rtmate command path
function getRtmateCommand(): string {
  // Try common locations
  const paths = [
    process.env.HOME + "/.local/bin/rtmate",
    "/usr/local/bin/rtmate",
    "/usr/bin/rtmate",
    "rtmate" // Fallback to PATH
  ]
  
  for (const path of paths) {
    if (path === "rtmate" || existsSync(path)) {
      return path
    }
  }
  
  throw new Error("rtmate not found. Install with: make install-client")
}

// Helper to execute rtmate command
function execRtmate(args: string[], options?: { cwd?: string; env?: Record<string, string>; timeout?: number }): string {
  const cmd = getRtmateCommand()
  
  // Escape arguments for shell execution
  const escapedArgs = args.map(arg => {
    // If argument contains spaces or special shell characters, wrap in single quotes
    // and escape existing single quotes
    if (/[\s"'&;()|<>]/.test(arg)) {
      return `'${arg.replace(/'/g, "'\\''")}'`
    }
    return arg
  })
  
  const fullCmd = [cmd, ...escapedArgs].join(" ")
  
  try {
    const result = execSync(fullCmd, {
      encoding: "utf-8",
      cwd: options?.cwd,
      env: { ...process.env, ...options?.env },
      stdio: ["pipe", "pipe", "pipe"],
      timeout: options?.timeout ?? 120000,
    })
    // Ensure result is a string
    const output = typeof result === "string" ? result : String(result || "")
    return output.trim()
  } catch (error: any) {
    const stderr = error.stderr?.toString() || error.message || String(error || "")
    throw new Error(`rtmate failed: ${stderr}`)
  }
}

// Get current host from state
function getCurrentHost(): string | null {
  const stateFile = join(process.env.HOME || "", ".local/share/remote-run/current-host")
  if (existsSync(stateFile)) {
    try {
      const content = readFileSync(stateFile, "utf-8")
      const contentStr = typeof content === "string" ? content : String(content || "")
      return contentStr.trim() || null
    } catch (error) {
      return null
    }
  }
  return null
}

// Get cached tmate links for a host
function getTmateLinks(host: string): { ssh?: string; web?: string } | null {
  const linksFile = join(process.env.HOME || "", `.local/share/remote-run/cache/${host}/tmate-links`)
  if (!existsSync(linksFile)) {
    return null
  }
  
  try {
    const content = readFileSync(linksFile, "utf-8")
    // Ensure content is a string - handle all possible types
    let contentStr: string
    if (typeof content === "string") {
      contentStr = content
    } else if (content != null && typeof content === "object" && "toString" in content) {
      contentStr = String(content)
    } else {
      contentStr = String(content || "")
    }
    
    // Additional safety check
    if (typeof contentStr !== "string" || !contentStr.split) {
      return null
    }
    
    const links: { ssh?: string; web?: string } = {}
    
    for (const line of contentStr.split("\n")) {
      if (line.startsWith("ssh: ")) {
        links.ssh = line.substring(5).trim()
      } else if (line.startsWith("web: ")) {
        links.web = line.substring(5).trim()
      }
    }
    
    return Object.keys(links).length > 0 ? links : null
  } catch (error) {
    return null
  }
}

/**
 * Initialize tmate session on remote server
 */
export const rtmateInit = tool({
  description: "Initialize tmate session on remote server. Sets up live terminal viewing for remote commands.",
  args: {
    host: tool.schema.string().describe("SSH host alias (from ~/.ssh/config)"),
    skipValidation: tool.schema.boolean().optional().describe("Skip session validation (faster)"),
  },
  async execute(args: { host: string; skipValidation?: boolean }) {
    const env: Record<string, string> = {}
    if (args.skipValidation) {
      env.TMATE_SKIP_VALIDATION = "1"
    }
    
    const output = execRtmate(["init", args.host], { env })
    
    // Extract links from output
    const links = getTmateLinks(args.host)
    
    let result = `Session initialized on ${args.host}.\n\n${output}`
    if (links) {
      result += `\n\nConnection links:\nSSH: ${links.ssh}\nWeb: ${links.web}`
    }
    result += `\n\nUse rtmateRun() to execute commands.`
    
    return result
  },
})

/**
 * Run command on remote server with stdout + mirroring to tmate
 */
export const rtmateRun = tool({
  description: "Execute command on remote server. Returns stdout/stderr AND mirrors to tmate session for live viewing.",
  args: {
    command: tool.schema.string().optional().describe("Command to execute (can include arguments)"),
    host: tool.schema.string().optional().describe("Override current host (optional)"),
    disableMirror: tool.schema.boolean().optional().describe("Disable mirroring to tmate"),
  },
  async execute(args: { command?: string; host?: string; disableMirror?: boolean } = {}) {
    const command = typeof args.command === "string" ? args.command : ""
    if (!command.trim()) {
      throw new Error("rtmateRun requires a non-empty command argument.")
    }

    const currentHost = getCurrentHost()
    if (!args.host && !currentHost) {
      throw new Error("No host configured. Run rtmateInit() first or provide host argument.")
    }
    
    const env: Record<string, string> = {}
    if (args.host) {
      env.REMOTE_HOST = args.host
    }
    if (args.disableMirror) {
      env.TMATE_RUN_MIRROR = "0"
    }
    
    const output = execRtmate(["run", command], { env })
    
    return `Command executed on ${args.host || currentHost}:\n\n${command}\n\nOutput:\n${output}\n\n(Output also mirrored to tmate session)`
  },
})

/**
 * Send command to tmate session (no stdout, output visible in tmate only)
 */
export const rtmateSend = tool({
  description: "Send command to tmate session. Output is visible in tmate only (no stdout returned). Use for interactive commands.",
  args: {
    command: tool.schema.string().describe("Command to send to tmate"),
    host: tool.schema.string().optional().describe("Override current host (optional)"),
  },
  async execute(args: { command: string; host?: string }) {
    const currentHost = getCurrentHost()
    if (!args.host && !currentHost) {
      throw new Error("No host configured. Run rtmateInit() first or provide host argument.")
    }
    
    // Safety check: Prevent sending multiple lines at once
    if (args.command.includes("\n")) {
      throw new Error("rtmateSend supports ONE command at a time. Do not send multiple lines.\n\nTo run multiple commands interactively, either:\n1. Call rtmateSend multiple times sequentially.\n2. Write a script using rtmateRun('printf ... > /tmp/script.sh') and then run it with rtmateSend('/tmp/script.sh').")
    }

    const env: Record<string, string> = {}
    if (args.host) {
      env.REMOTE_HOST = args.host
    }
    
    execRtmate(["send", args.command], { env })
    
    return `Command sent to tmate session on ${args.host || currentHost}:\n\n${args.command}\n\n(Output visible in tmate session only, not returned here)`
  },
})

/**
 * Read content from tmate session
 */
export const rtmateRead = tool({
  description: "Read content from the remote tmate session. Useful to see output of interactive commands sent via rtmateSend.",
  args: {
    host: tool.schema.string().optional().describe("Override current host (optional)"),
    lines: tool.schema.number().optional().describe("Number of lines to read from the bottom (default: full visible pane)"),
  },
  async execute(args: { host?: string; lines?: number }) {
    const currentHost = getCurrentHost()
    if (!args.host && !currentHost) {
      throw new Error("No host configured. Run rtmateInit() first or provide host argument.")
    }
    
    const cmdArgs = ["read"]
    if (args.host) {
      cmdArgs.push(args.host)
    }
    if (args.lines) {
      cmdArgs.push("-n", args.lines.toString())
    }
    
    const output = execRtmate(cmdArgs)
    
    return `Terminal content from ${args.host || currentHost}:\n\n${output}`
  },
})

/**
 * Get current rtmate status
 */
export const rtmateStatus = tool({
  description: DESCRIPTION,
  args: {},
  async execute(_args: {}) {
    const currentHost = getCurrentHost()
    if (!currentHost) {
      return `Tool version: ${TOOL_VERSION}\nNo session initialized. Run rtmateInit() first.`
    }
    
    const links = getTmateLinks(currentHost)
    
    if (links) {
      return `Tool version: ${TOOL_VERSION}\nActive session on ${currentHost}.\nConnect via SSH: ${links.ssh}\nConnect via Web: ${links.web}`
    } else {
      return `Tool version: ${TOOL_VERSION}\nActive session on ${currentHost} but links not cached.`
    }
  },
})
