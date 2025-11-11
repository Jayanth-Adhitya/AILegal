"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { negotiationApi } from "@/lib/api";
import type { Negotiation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  MessageSquare,
  AlertCircle,
} from "lucide-react";
import { ChatInterface } from "@/components/negotiations/ChatInterface";
import { useAuth } from "@/contexts/AuthContext";

export default function NegotiationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const negotiationId = params.id as string;

  const [negotiation, setNegotiation] = useState<Negotiation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);

  useEffect(() => {
    loadNegotiation();
  }, [negotiationId]);

  const loadNegotiation = async () => {
    try {
      setLoading(true);
      const data = await negotiationApi.getNegotiation(negotiationId);
      setNegotiation(data);
    } catch (err: any) {
      setError(err.message || "Failed to load negotiation");
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    try {
      setActionLoading(true);
      await negotiationApi.acceptNegotiation(negotiationId);
      await loadNegotiation();
    } catch (err: any) {
      setError(err.message || "Failed to accept negotiation");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    try {
      setActionLoading(true);
      await negotiationApi.rejectNegotiation(negotiationId);
      setShowRejectDialog(false);
      router.push("/negotiations");
    } catch (err: any) {
      setError(err.message || "Failed to reject negotiation");
    } finally {
      setActionLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      setActionLoading(true);
      await negotiationApi.completeNegotiation(negotiationId);
      setShowCompleteDialog(false);
      await loadNegotiation();
    } catch (err: any) {
      setError(err.message || "Failed to complete negotiation");
    } finally {
      setActionLoading(false);
    }
  };

  const getOtherParty = () => {
    if (!negotiation || !user) return null;
    return negotiation.initiator_user_id === user.id
      ? negotiation.receiver
      : negotiation.initiator;
  };

  const isReceiver = negotiation && user && negotiation.receiver_user_id === user.id;
  const isInitiator = negotiation && user && negotiation.initiator_user_id === user.id;
  const otherParty = getOtherParty();

  const getStatusBadge = (status: Negotiation["status"]) => {
    const variants: Record<Negotiation["status"], { variant: any; icon: any; label: string }> = {
      pending: { variant: "secondary", icon: Clock, label: "Pending" },
      active: { variant: "default", icon: MessageSquare, label: "Active" },
      completed: { variant: "default", icon: CheckCircle2, label: "Completed" },
      rejected: { variant: "destructive", icon: XCircle, label: "Rejected" },
      cancelled: { variant: "outline", icon: XCircle, label: "Cancelled" },
    };

    const config = variants[status];
    const Icon = config.icon;

    return (
      <Badge variant={config.variant as any} className="gap-1">
        <Icon className="h-4 w-4" />
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Skeleton className="h-8 w-64 mb-6" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-4 w-1/3 mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-96" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !negotiation) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error || "Negotiation not found"}</AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/negotiations")} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Negotiations
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/negotiations")}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Negotiations
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {negotiation.contract_name}
              </h1>
              {getStatusBadge(negotiation.status)}
            </div>
            <div className="flex items-center gap-4 text-gray-600">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                <span>{otherParty?.company_name || "Unknown Company"}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span>Created {new Date(negotiation.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            {negotiation.status === "pending" && isReceiver && (
              <>
                <Button
                  onClick={handleAccept}
                  disabled={actionLoading}
                  size="lg"
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Accept
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setShowRejectDialog(true)}
                  disabled={actionLoading}
                  size="lg"
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
              </>
            )}

            {negotiation.status === "active" && (
              <Button
                variant="outline"
                onClick={() => setShowCompleteDialog(true)}
                disabled={actionLoading}
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Mark as Complete
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Pending Message */}
      {negotiation.status === "pending" && isInitiator && (
        <Alert className="mb-6">
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Waiting for {otherParty?.company_name} to accept your negotiation request.
          </AlertDescription>
        </Alert>
      )}

      {negotiation.status === "pending" && isReceiver && (
        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {otherParty?.company_name} wants to negotiate "{negotiation.contract_name}" with
            you. Accept to start chatting.
          </AlertDescription>
        </Alert>
      )}

      {/* Chat Interface */}
      {negotiation.status === "active" && (
        <Card>
          <CardHeader>
            <CardTitle>Negotiation Chat</CardTitle>
            <CardDescription>
              Discuss contract terms with {otherParty?.company_name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChatInterface negotiationId={negotiationId} />
          </CardContent>
        </Card>
      )}

      {/* Completed/Rejected Message */}
      {(negotiation.status === "completed" ||
        negotiation.status === "rejected" ||
        negotiation.status === "cancelled") && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            This negotiation is {negotiation.status}. Chat is read-only.
          </AlertDescription>
        </Alert>
      )}

      {/* Reject Dialog */}
      <AlertDialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reject Negotiation Request?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to reject this negotiation request from{" "}
              {otherParty?.company_name}? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleReject} className="bg-destructive">
              Reject
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Complete Dialog */}
      <AlertDialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Mark as Complete?</AlertDialogTitle>
            <AlertDialogDescription>
              Mark this negotiation as completed? The chat will become read-only.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleComplete}>
              Mark Complete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
