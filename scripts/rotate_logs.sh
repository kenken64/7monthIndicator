#!/bin/bash
# Standalone log rotation script for trading bot system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_header() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}🗂️  Trading Bot Log Rotation Utility${NC}"
    echo -e "${PURPLE}================================================${NC}"
    echo ""
}

# Compression function for rotated logs
compress_rotated_logs() {
    local compressed_count=0
    local total_compressed_size=0
    local total_original_size=0
    
    print_info "🗜️  Compressing individual rotated logs..."
    
    # Find all .log files in rotated directory that aren't already compressed
    while IFS= read -r -d '' logfile; do
        if [ -f "$logfile" ]; then
            local filename=$(basename "$logfile")
            local original_size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo "0")
            local archive_name="${filename%.log}.tar.gz"
            local archive_path="$PROJECT_ROOT/logs/rotated/$archive_name"
            
            # Create individual compressed archive
            cd "$PROJECT_ROOT/logs/rotated"
            tar -czf "$archive_name" "$filename" 2>/dev/null
            
            if [ $? -eq 0 ] && [ -f "$archive_path" ]; then
                local compressed_size=$(stat -f%z "$archive_path" 2>/dev/null || stat -c%s "$archive_path" 2>/dev/null || echo "0")
                local original_mb=$((original_size / 1048576))
                local compressed_mb=$((compressed_size / 1048576))
                local savings_percent=$(( (original_size - compressed_size) * 100 / original_size ))
                
                # Remove original log file after successful compression
                rm "$logfile"
                
                print_status "🗜️  Compressed: $filename (${original_mb}MB → ${compressed_mb}MB, ${savings_percent}% saved)"
                compressed_count=$((compressed_count + 1))
                total_original_size=$((total_original_size + original_size))
                total_compressed_size=$((total_compressed_size + compressed_size))
            else
                print_error "Failed to compress $filename"
            fi
            cd "$PROJECT_ROOT"
        fi
    done < <(find "$PROJECT_ROOT/logs/rotated" -maxdepth 1 -name "*.log" -type f -print0)
    
    if [ $compressed_count -gt 0 ]; then
        local total_original_mb=$((total_original_size / 1048576))
        local total_compressed_mb=$((total_compressed_size / 1048576))
        local total_savings=$((total_original_size - total_compressed_size))
        local total_savings_mb=$((total_savings / 1048576))
        local total_savings_percent=$(( total_savings * 100 / total_original_size ))
        
        print_status "📦 Compression Summary:"
        echo -e "${GREEN}   ✅ Compressed: $compressed_count files${NC}"
        echo -e "${GREEN}   💾 Original size: ${total_original_mb}MB${NC}"
        echo -e "${GREEN}   🗜️  Compressed size: ${total_compressed_mb}MB${NC}"
        echo -e "${GREEN}   💰 Space saved: ${total_savings_mb}MB (${total_savings_percent}%)${NC}"
    else
        print_info "📝 No uncompressed log files found to compress"
    fi
}

# Enhanced log rotation function
rotate_logs() {
    local size_threshold=${1:-1M}  # Default 1MB, can be overridden
    local max_age_days=${2:-7}     # Default 7 days, can be overridden
    local compress=${3:-true}      # Default true, compress rotated logs
    
    print_info "🔄 Starting log rotation (threshold: $size_threshold, cleanup: ${max_age_days}d, compress: $compress)"
    
    # Define log directories and files to rotate
    local log_paths=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT"
        "$PROJECT_ROOT/services/trading"
        "$PROJECT_ROOT/services/chart-analysis"
        "$PROJECT_ROOT/services/mcp-server"
        "$PROJECT_ROOT/services/web-dashboard"
    )
    
    # Create rotated logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs/rotated"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local rotated_count=0
    local total_size_saved=0
    
    # Find and rotate log files larger than threshold
    for log_dir in "${log_paths[@]}"; do
        if [ -d "$log_dir" ]; then
            print_info "📁 Checking directory: $log_dir"
            
            # Find .log files larger than threshold
            while IFS= read -r -d '' logfile; do
                if [ -f "$logfile" ]; then
                    local filename=$(basename "$logfile")
                    local file_size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo "0")
                    local size_mb=$((file_size / 1048576))
                    local rotated_name="${filename%.log}_${timestamp}.log"
                    
                    # Move the log file to rotated directory
                    mv "$logfile" "$PROJECT_ROOT/logs/rotated/$rotated_name"
                    
                    # Create a new empty log file with same permissions
                    touch "$logfile"
                    chmod 644 "$logfile"
                    
                    print_status "📦 Rotated: $filename (${size_mb}MB) → rotated/$rotated_name"
                    rotated_count=$((rotated_count + 1))
                    total_size_saved=$((total_size_saved + file_size))
                fi
            done < <(find "$log_dir" -maxdepth 1 -name "*.log" -size "+$size_threshold" -type f -print0)
        fi
    done
    
    # Compress rotated logs if enabled
    if [ "$compress" = "true" ]; then
        compress_rotated_logs
    fi
    
    # Clean up old files (compressed archives and uncompressed logs)
    print_info "🧹 Cleaning up old files older than ${max_age_days} days..."
    local cleaned_logs=$(find "$PROJECT_ROOT/logs/rotated" -name "*.log" -type f -mtime "+$max_age_days" -delete -print 2>/dev/null | wc -l)
    local cleaned_archives=$(find "$PROJECT_ROOT/logs/rotated" -name "*.tar.gz" -type f -mtime "+$max_age_days" -delete -print 2>/dev/null | wc -l)
    local cleaned_count=$((cleaned_logs + cleaned_archives))
    
    # Generate summary report
    echo ""
    print_info "📊 Log Rotation Summary:"
    if [ $rotated_count -eq 0 ]; then
        echo -e "${BLUE}   📝 No logs required rotation (all < $size_threshold)${NC}"
    else
        local size_saved_mb=$((total_size_saved / 1048576))
        echo -e "${GREEN}   ✅ Rotated: $rotated_count log files${NC}"
        echo -e "${GREEN}   💾 Space reclaimed: ${size_saved_mb}MB${NC}"
    fi
    
    if [ "$cleaned_count" -gt 0 ]; then
        echo -e "${BLUE}   🗑️  Cleaned up: $cleaned_count old rotated logs${NC}"
    fi
    
    # Show current log sizes
    echo ""
    print_info "📈 Current log file sizes:"
    for log_dir in "${log_paths[@]}"; do
        if [ -d "$log_dir" ]; then
            find "$log_dir" -maxdepth 1 -name "*.log" -type f -exec ls -lah {} \; | while read -r line; do
                echo -e "${BLUE}   $(echo "$line" | awk '{print $5 "  " $9}')${NC}"
            done 2>/dev/null
        fi
    done | sort -k1 -hr | head -10
}

# Main execution
print_header

case "${1:-rotate}" in
    "rotate")
        rotate_logs "${2:-1M}" "${3:-7}" "${4:-true}"
        ;;
    "force")
        print_info "🚨 Force rotation (all .log files regardless of size)"
        rotate_logs "0" "${2:-7}" "${3:-true}"
        ;;
    "compress")
        print_info "🗜️  Compressing existing rotated logs only..."
        compress_rotated_logs
        ;;
    "clean")
        print_info "🗑️  Cleaning old rotated files only..."
        local cleaned_logs=$(find "$PROJECT_ROOT/logs/rotated" -name "*.log" -type f -mtime "+${2:-7}" -delete -print 2>/dev/null | wc -l)
        local cleaned_archives=$(find "$PROJECT_ROOT/logs/rotated" -name "*.tar.gz" -type f -mtime "+${2:-7}" -delete -print 2>/dev/null | wc -l)
        local total_cleaned=$((cleaned_logs + cleaned_archives))
        echo "Cleaned up $total_cleaned files (${cleaned_logs} logs, ${cleaned_archives} archives)"
        ;;
    "help"|"--help"|"-h")
        echo "Usage: $0 [command] [size_threshold] [max_age_days] [compress]"
        echo ""
        echo "Commands:"
        echo "  rotate [1M] [7] [true]  - Rotate logs larger than size threshold (default: 1M, cleanup: 7 days, compress: true)"
        echo "  force [7] [true]        - Force rotate all .log files regardless of size (cleanup: 7 days, compress: true)"  
        echo "  compress                - Only compress existing rotated .log files"
        echo "  clean [7]               - Only clean up old rotated files (default: 7 days)"
        echo "  help                    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                       # Rotate logs > 1MB, cleanup > 7 days, compress"
        echo "  $0 rotate 500K 3 false   # Rotate logs > 500KB, cleanup > 3 days, no compression"
        echo "  $0 force                 # Force rotate all logs with compression"
        echo "  $0 compress              # Compress existing rotated logs only"
        echo "  $0 clean 14              # Clean rotated files older than 14 days"
        exit 0
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

echo ""
print_status "🎯 Log rotation completed successfully!"