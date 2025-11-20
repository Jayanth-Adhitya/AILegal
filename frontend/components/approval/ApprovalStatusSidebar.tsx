"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Users,
  FileSignature,
  Mail,
  AlertCircle,
  User,
  Calendar,
  MessageSquare,
} from "lucide-react";
import { format } from "date-fns";

interface Party {
  id: string;
  name: string;
  email: string;
  role?: string;
}

interface ApprovalRecord {
  id: string;
  party: Party;
  status: "pending" | "reviewing" | "approved" | "rejected";
  timestamp?: string;
  comments?: string;
}

interface SignatureRecord {
  id: string;
  signer_name: string;
  signer_email: string;
  signed_at?: string;
  signature_type: "drawn" | "typed";
  is_valid: boolean;
  status: "pending" | "completed" | "expired";
}

interface ApprovalStatusSidebarProps {
  documentId: string;
  currentUserId?: string;
  approvals?: ApprovalRecord[];
  signatures?: SignatureRecord[];
  onApprove?: () => void;
  onReject?: () => void;
  onRequestSignature?: () => void;
  showActions?: boolean;
}

export function ApprovalStatusSidebar({
  documentId,
  currentUserId,
  approvals = [],
  signatures = [],
  onApprove,
  onReject,
  onRequestSignature,
  showActions = true,
}: ApprovalStatusSidebarProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [realtimeApprovals, setRealtimeApprovals] = useState<ApprovalRecord[]>(approvals);
  const [realtimeSignatures, setRealtimeSignatures] = useState<SignatureRecord[]>(signatures);

  // Calculate progress
  const approvedCount = realtimeApprovals.filter(a => a.status === "approved").length;
  const totalParties = realtimeApprovals.length || 1;
  const approvalProgress = (approvedCount / totalParties) * 100;

  const signedCount = realtimeSignatures.filter(s => s.status === "completed").length;
  const totalSignatures = realtimeSignatures.length || 1;
  const signatureProgress = (signedCount / totalSignatures) * 100;

  const allPartiesApproved = approvedCount === totalParties && totalParties > 0;
  const allSignaturesComplete = signedCount === totalSignatures && totalSignatures > 0;

  // WebSocket connection for real-time updates
  useEffect(() => {
    // TODO: Implement WebSocket connection for real-time updates
    // const ws = new WebSocket(`${WS_URL}/ws/document/${documentId}/status`);
    // ws.onmessage = (event) => {
    //   const update = JSON.parse(event.data);
    //   // Update approvals and signatures
    // };
    setIsConnected(true);

    return () => {
      // Clean up WebSocket connection
      setIsConnected(false);
    };
  }, [documentId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "rejected":
      case "expired":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "reviewing":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      approved: "default",
      completed: "default",
      rejected: "destructive",
      expired: "destructive",
      reviewing: "secondary",
      pending: "outline",
    };

    return (
      <Badge variant={variants[status] || "outline"} className="capitalize">
        {status}
      </Badge>
    );
  };

  return (
    <Card className="w-80 h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg">Document Status</span>
          {isConnected && (
            <Badge variant="outline" className="text-xs">
              <span className="h-2 w-2 bg-green-500 rounded-full mr-1 animate-pulse" />
              Live
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <ScrollArea className="h-[calc(100vh-200px)]">
        <CardContent className="space-y-6">
          {/* Approval Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <span className="font-medium">Approvals</span>
              </div>
              <span className="text-sm text-gray-500">
                {approvedCount} of {totalParties}
              </span>
            </div>

            <Progress value={approvalProgress} className="mb-3" />

            <div className="space-y-2">
              {realtimeApprovals.length > 0 ? (
                realtimeApprovals.map((approval) => (
                  <div
                    key={approval.id}
                    className="flex items-start justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <div className="flex items-start gap-2">
                      {getStatusIcon(approval.status)}
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {approval.party.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {approval.party.email}
                        </div>
                        {approval.timestamp && (
                          <div className="text-xs text-gray-400 mt-1">
                            {format(new Date(approval.timestamp), "MMM d, h:mm a")}
                          </div>
                        )}
                        {approval.comments && (
                          <div className="mt-1 p-1 bg-white rounded text-xs">
                            <MessageSquare className="h-3 w-3 inline mr-1" />
                            {approval.comments}
                          </div>
                        )}
                      </div>
                    </div>
                    {getStatusBadge(approval.status)}
                  </div>
                ))
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  No approval records yet
                </div>
              )}
            </div>

            {showActions && !allPartiesApproved && (
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onApprove}
                  className="flex-1"
                >
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={onReject}
                  className="flex-1"
                >
                  <XCircle className="h-3 w-3 mr-1" />
                  Reject
                </Button>
              </div>
            )}

            {allPartiesApproved && (
              <div className="mt-3 p-2 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 text-green-700 text-sm">
                  <CheckCircle2 className="h-4 w-4" />
                  All parties have approved
                </div>
              </div>
            )}
          </div>

          <Separator />

          {/* Signature Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <FileSignature className="h-4 w-4" />
                <span className="font-medium">Signatures</span>
              </div>
              <span className="text-sm text-gray-500">
                {signedCount} of {totalSignatures}
              </span>
            </div>

            <Progress value={signatureProgress} className="mb-3" />

            <div className="space-y-2">
              {realtimeSignatures.length > 0 ? (
                realtimeSignatures.map((signature) => (
                  <div
                    key={signature.id}
                    className="flex items-start justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <div className="flex items-start gap-2">
                      {getStatusIcon(signature.status)}
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {signature.signer_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {signature.signer_email}
                        </div>
                        {signature.signed_at && (
                          <div className="text-xs text-gray-400 mt-1">
                            {format(new Date(signature.signed_at), "MMM d, h:mm a")}
                          </div>
                        )}
                        <div className="text-xs text-gray-400">
                          Type: {signature.signature_type}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1">
                      {getStatusBadge(signature.status)}
                      {signature.status === "completed" && !signature.is_valid && (
                        <Badge variant="destructive" className="text-xs">
                          Invalid
                        </Badge>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  No signatures requested yet
                </div>
              )}
            </div>

            {showActions && allPartiesApproved && !allSignaturesComplete && (
              <Button
                size="sm"
                onClick={onRequestSignature}
                className="w-full mt-3"
              >
                <Mail className="h-3 w-3 mr-1" />
                Request Signatures
              </Button>
            )}

            {allSignaturesComplete && (
              <div className="mt-3 p-2 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 text-green-700 text-sm">
                  <CheckCircle2 className="h-4 w-4" />
                  Document fully executed
                </div>
              </div>
            )}
          </div>

          {/* Timeline Section (Optional) */}
          <Separator />
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Calendar className="h-4 w-4" />
              <span className="font-medium">Activity Timeline</span>
            </div>
            <div className="text-xs text-gray-500 text-center py-4">
              Coming soon...
            </div>
          </div>
        </CardContent>
      </ScrollArea>
    </Card>
  );
}