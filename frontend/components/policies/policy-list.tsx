"use client";

import { useState } from "react";
import { FileText, Trash2, Search, Eye, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Policy } from "@/lib/types";
import { formatDate, formatFileSize } from "@/lib/utils";
import { policyApi } from "@/lib/api";
import Link from "next/link";

interface PolicyListProps {
  policies: Policy[];
  onPolicyDeleted: () => void;
}

export function PolicyList({ policies, onPolicyDeleted }: PolicyListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; policy: Policy | null }>({
    open: false,
    policy: null,
  });
  const [deleting, setDeleting] = useState(false);

  const filteredPolicies = policies.filter(
    (policy) =>
      policy.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (policy.policy_number?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleDelete = async () => {
    if (!deleteDialog.policy) return;

    setDeleting(true);
    try {
      await policyApi.deletePolicy(deleteDialog.policy.id);
      setDeleteDialog({ open: false, policy: null });
      onPolicyDeleted();
    } catch (error) {
      console.error("Failed to delete policy:", error);
    } finally {
      setDeleting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      active: { color: "bg-green-100 text-green-800", icon: CheckCircle2 },
      draft: { color: "bg-yellow-100 text-yellow-800", icon: Clock },
      archived: { color: "bg-gray-100 text-gray-800", icon: AlertCircle },
    };
    const variant = variants[status as keyof typeof variants] || variants.active;
    const Icon = variant.icon;

    return (
      <Badge variant="secondary" className={variant.color}>
        <Icon className="mr-1 h-3 w-3" />
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search by title or policy number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {filteredPolicies.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-sm font-medium text-gray-900">
            {searchQuery ? "No policies found" : "No policies uploaded yet"}
          </p>
          <p className="mt-2 text-sm text-gray-500">
            {searchQuery
              ? "Try adjusting your search"
              : "Upload your first policy to get started"}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Policy Number</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Sections</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="w-[150px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPolicies.map((policy) => (
                <TableRow key={policy.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-blue-600" />
                      <Link href={`/policies/${policy.id}`} className="hover:underline">
                        {policy.title}
                      </Link>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {policy.policy_number || "N/A"}
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {policy.version}
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {(policy as any).section_count || 0} sections
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(policy.status)}
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {formatDate(policy.updated_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Link href={`/policies/${policy.id}`}>
                        <Button variant="ghost" size="icon" title="View">
                          <Eye className="h-4 w-4 text-blue-600" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Delete"
                        onClick={() => setDeleteDialog({ open: true, policy })}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, policy: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Policy</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{deleteDialog.policy?.title}&quot;? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialog({ open: false, policy: null })}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
